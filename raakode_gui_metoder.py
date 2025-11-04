import sys
import numpy as np
import threading
import time
from PyQt6.QtWidgets import QApplication, QLineEdit, QDial, QPushButton, QMainWindow, QLCDNumber, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

sensor_data = {
    "x": np.linspace(0, 2*np.pi, 100),
    "y": np.zeros(100),
    "dy": np.zeros(100)   # store derivative too
}
delta_t=0.05

stopp_trigger = threading.Event()

def sensor_loop():
    while not stopp_trigger.is_set():
        sensor_data["y"] = np.sin(sensor_data["x"] + time.time())
        sensor_data["dy"] = np.gradient(sensor_data["y"], delta_t)
        time.sleep(delta_t)

class Mpl_grafer(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ELE340 - Gruppe E")

        # Setter opp ønsket layout på GUI: 3 blokker horisontalt med undergrupper for: Grafer, setpunkt, start/stopp
        gridman = QHBoxLayout()
        subgrid_1 = QVBoxLayout()
        subgrid_2 = QVBoxLayout()
        subgrid_3 = QVBoxLayout()

        # Setter opp Graf 1 og 2, test-signaler hardkoda inn for nå, må endres til å kunne motta et hvilket som helst signal
        self.graf = Mpl_grafer(self)
        self.line, = self.graf.ax.plot(sensor_data["x"], sensor_data["y"], color="blue")

        self.graf_deriv = Mpl_grafer(self)
        self.line_deriv, = self.graf_deriv.ax.plot(sensor_data["x"], sensor_data["dy"], color="red")

        subgrid_1.addWidget(self.graf)
        subgrid_1.addWidget(self.graf_deriv)

        # Setter opp en timer for å automatisk oppdatere plottene, må kanskje løses på en annen måte med faktiske signaler
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()


        self.LCD = QLCDNumber()
        self.LCD.display(30)

        self.tekstboks = QLineEdit()
        self.knapp_set = QPushButton("Sett distanse")

        subgrid_2.addWidget(self.LCD)
        subgrid_2.addWidget(self.tekstboks)
        subgrid_2.addWidget(self.knapp_set)



        self.knapp_start = QPushButton("Start")
        self.knapp_stopp = QPushButton("Stopp")
        subgrid_3.addWidget(self.knapp_start)
        subgrid_3.addWidget(self.knapp_stopp)

        gridman.addLayout(subgrid_1)
        gridman.addLayout(subgrid_2)
        gridman.addLayout(subgrid_3)

        # Setter opp knapp til å sette verdi fra tekstboks til LCD
        self.knapp_set.clicked.connect(self.update_LCD)
        self.y_shift = 0

        self.knapp_start.clicked.connect(self.start_kommando)
        self.knapp_stopp.clicked.connect(self.stopp_kommando)



        widget = QWidget()
        widget.setLayout(gridman)
        self.setCentralWidget(widget)

    def start_kommando(self):
        print("k")   

    def stopp_kommando(self):
        print("s")
        stopp_trigger.set()
        self.timer.stop()
        QApplication.quit()

    def update_plot(self):
        self.line.set_ydata(sensor_data["y"] + self.y_shift)
        self.line_deriv.set_ydata(sensor_data["dy"])
        self.graf.draw()
        self.graf_deriv.draw()
    
    def update_LCD(self):
        text = self.tekstboks.text()
        try:
            verdi = float(text)
            if 20 < verdi < 150:
                self.LCD.display(verdi)
                self.y_shift = verdi
            else:
                print("Vennligst skriv et tall innenfor 20 og 150 [cm].")
        except ValueError:
            print("Vennligst skriv et tall innenfor 20 og 150 [cm].")



if __name__ == "__main__":
    thread1 = threading.Thread(target=sensor_loop, daemon=True)
    thread1.start()

applikasjon = QApplication(sys.argv)
vindu = MainWindow()
vindu.show()
applikasjon.exec()