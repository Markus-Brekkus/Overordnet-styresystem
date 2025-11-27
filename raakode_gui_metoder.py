import sys
import numpy as np
import threading
import time
from PyQt6.QtWidgets import QApplication, QLineEdit, QDial, QPushButton, QMainWindow, QLCDNumber, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import kommando_status
import serial

# Oppsett for innhenting og stopping av sensordata ----------------
delta_t = 0.05 # Periodetid for sampling i live-plottet
maalinger_n = 100 # Antall målinger som beholdes i live-plottet
stopp_trigger = threading.Event()

sensor_data = { #Array som holder på sensormålingene
    "x": np.linspace(0, delta_t*maalinger_n, 100),
    "y": np.zeros(maalinger_n),
    "dy": np.zeros(maalinger_n)   
}

def sensor_loop(): #Funksjon som setter inn måleverdien fra sensor og rullerer verdiene videre slik at datasettet som plottes alltid er maalinger_n langt.
    while not stopp_trigger.is_set():

        sensor_data["y"][:-1] = sensor_data["y"][1:]
        sensor_data["dy"][:-1] = sensor_data["dy"][1:]

        sensor_data["y"][-1] = kommando_status.maaleverdi
        sensor_data["dy"][-1] = kommando_status.error        


        #print(sensor_data["dy"])
        
        time.sleep(delta_t)
# ---------------------------------------------------------------

serieport = serial.Serial(
    port='COM13',
    baudrate=115200,
    bytesize=serial.EIGHTBITS,   # 8 data bits
    parity=serial.PARITY_NONE,   # No parity
    stopbits=serial.STOPBITS_ONE, # 1 stop bit
    timeout=1
)

def send_RPID(RPID_verdier):
    serieport.write(RPID_verdier)
    

def BE_til_LE(hexverdi):
    return bytes([hexverdi & 0xFF, (hexverdi>>8) & 0xFF])

# Oppsett av grafer til GUI ----------------------------
class Mpl_grafer(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
#------------------------------------------------------

# GUI hovedvindu -------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ELE340 - Gruppe E")

        # Setter opp ønsket layout på GUI: 3 blokker horisontalt med undergrupper for: Grafer, setpunkt, start/stopp
        gridman = QVBoxLayout()

        subgrid_graf = QVBoxLayout()
        subgrid_HMI = QHBoxLayout()

        Ref_modul = QVBoxLayout()
        Kp_modul = QVBoxLayout()
        Ti_modul = QVBoxLayout()
        Td_modul = QVBoxLayout()
        knapp_modul = QVBoxLayout()

        # Setter opp Graf 1 og 2, per nå er graf 1 bare en avlesning av X-retning på aks-måler, og 2 er den deriverte av dette
        self.graf = Mpl_grafer(self)
        self.line, = self.graf.ax.plot(sensor_data["x"], sensor_data["y"], color="blue")

        self.graf_deriv = Mpl_grafer(self)
        self.line_deriv, = self.graf_deriv.ax.plot(sensor_data["x"], sensor_data["dy"], color="red")


        # Setter opp en timer for å automatisk oppdatere plottene
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        # Setter opp numerisk display og knapper
        self.Ref_LCD = QLCDNumber()
        self.Ref_LCD.display(kommando_status.Ref_iv)
        self.Ref_txt = QLineEdit()

        self.Kp_LCD = QLCDNumber()
        self.Kp_LCD.display(kommando_status.Kp_iv)
        self.Kp_txt = QLineEdit()

        self.Ti_LCD = QLCDNumber()
        self.Ti_LCD.display(kommando_status.Ti_iv)
        self.Ti_txt = QLineEdit()

        self.Td_LCD = QLCDNumber()
        self.Td_LCD.display(kommando_status.Td_iv)
        self.Td_txt = QLineEdit()

        self.knapp_start = QPushButton("Start")
        self.knapp_stopp = QPushButton("Stopp")
        self.knapp_set = QPushButton("Sett distanse")

        #Setter opp innhold i subgrids
        subgrid_graf.addWidget(self.graf)
        subgrid_graf.addWidget(self.graf_deriv)
        
        Ref_modul.addWidget(self.Ref_LCD)
        Ref_modul.addWidget(self.Ref_txt)

        Kp_modul.addWidget(self.Kp_LCD)
        Kp_modul.addWidget(self.Kp_txt)

        Ti_modul.addWidget(self.Ti_LCD)
        Ti_modul.addWidget(self.Ti_txt)
        
        Td_modul.addWidget(self.Td_LCD)
        Td_modul.addWidget(self.Td_txt)
        
        knapp_modul.addWidget(self.knapp_start)
        knapp_modul.addWidget(self.knapp_set)
        knapp_modul.addWidget(self.knapp_stopp)

        subgrid_HMI.addLayout(Ref_modul)
        subgrid_HMI.addLayout(Kp_modul)
        subgrid_HMI.addLayout(Ti_modul)
        subgrid_HMI.addLayout(Td_modul)
        subgrid_HMI.addLayout(knapp_modul)

        gridman.addLayout(subgrid_graf)
        gridman.addLayout(subgrid_HMI)

        # Setter opp sknapp-events
        self.knapp_set.clicked.connect(self.update_LCD)
        self.y_shift = 0

        self.knapp_start.clicked.connect(self.start_kommando)
        self.knapp_stopp.clicked.connect(self.stopp_kommando)



        widget = QWidget()
        widget.setLayout(gridman)
        self.setCentralWidget(widget)

    # Div funksjoner for knapp-events og oppdatering av GUI-elementer
    def start_kommando(self):
        print("k")   
        kommando_status.start_event.set()
        kommando='k'
        status = 'k'
        RPID = (BE_til_LE(kommando_status.Ref_iv))+(BE_til_LE(kommando_status.Kp_iv))+(BE_til_LE(kommando_status.Ti_iv))+(BE_til_LE(kommando_status.Td_iv))
        print(RPID)
        send_RPID(RPID)        
        

    def stopp_kommando(self):
        RPID = (BE_til_LE(300))+(BE_til_LE(0))+(BE_til_LE(0))+(BE_til_LE(0))
        print(RPID)
        send_RPID(RPID)
        print("s")
        kommando_status.stopp_event.set()
        stopp_trigger.set()
        self.timer.stop()
        QApplication.quit()

    def update_plot(self):
        self.line.set_ydata(sensor_data["y"] + self.y_shift)
        self.line_deriv.set_ydata(sensor_data["dy"])

        ax = self.line.axes
        ax_deriv = self.line_deriv.axes
    
        # autoscale both plots
        ax.relim()
        ax.autoscale_view()
        ax_deriv.relim()
        ax_deriv.autoscale_view()
        
        self.graf.draw()
        self.graf_deriv.draw()
    
    def update_LCD(self):
        Ref_raa = self.Ref_txt.text()
        Kp_raa = self.Kp_txt.text()
        Ti_raa = self.Ti_txt.text()
        Td_raa = self.Td_txt.text()

        try:
            print(1)
            Ref_verdi = int(Ref_raa)*10
            print(2)
            Kp_verdi = int(float(Kp_raa)*1000)
            Ti_verdi = int(float(Ti_raa)*1000)
            Td_verdi = int(float(Td_raa)*1000)
            print(3)
            print(Ref_verdi)
            print(Kp_verdi)
            print(Ti_verdi)
            print(Td_verdi)
            if 10 < int(Ref_raa) < 400:
                self.Ref_LCD.display(float(Ref_raa))   
            else:
                print("Vennligst skriv et tall innenfor 20 og 150 [cm].")
            self.Kp_LCD.display(Kp_raa)
            self.Ti_LCD.display(Ti_raa)
            self.Td_LCD.display(Td_raa)
            RPID = (BE_til_LE(Ref_verdi))+(BE_til_LE(Kp_verdi))+(BE_til_LE(Ti_verdi))+(BE_til_LE(Td_verdi))
            print(RPID)
            send_RPID(RPID)



        except ValueError:
            print("Vennligst skriv et tall innenfor 20 og 150 [cm].")
#------------------------------------------------------------------


if __name__ == "__main__":
    thread1 = threading.Thread(target=sensor_loop, daemon=True)
    thread1.start()

    applikasjon = QApplication(sys.argv)
    vindu = MainWindow()
    vindu.show()
    applikasjon.exec()
    serieport.close()