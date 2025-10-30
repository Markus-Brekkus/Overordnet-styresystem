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
    "y": np.zeros(100)
}

def sensor_loop():
    while True:
        sensor_data["y"] = np.sin(sensor_data["x"] + time.time())
        time.sleep(0.05)

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

        gridman = QHBoxLayout()
        subgrid_1 = QVBoxLayout()
        subgrid_2 = QVBoxLayout()

        self.graf = Mpl_grafer(self)
        self.line, = self.graf.ax.plot(sensor_data["x"], sensor_data["y"], color="blue")

        self.graf_deriv = Mpl_grafer(self)
        self.line_deriv = self.graf_deriv.ax.plot(sensor_data["x"], sensor_data["y"], color="red")

        subgrid_1.addWidget(self.graf)

        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()


        self.LCD = QLCDNumber()
        self.tekstboks = QLineEdit()
        self.knapp_set = QPushButton("Sett distanse")

        subgrid_2.addWidget(self.LCD)
        subgrid_2.addWidget(self.tekstboks)
        subgrid_2.addWidget(self.knapp_set)

        gridman.addLayout(subgrid_1)
        gridman.addLayout(subgrid_2)

        # Setter opp knapp til å sette verdi fra tekstboks til LCD
        self.knapp_set.clicked.connect(self.update_LCD)
        self.y_shift = 0



        widget = QWidget()
        widget.setLayout(gridman)
        self.setCentralWidget(widget)

        
    
    def update_plot(self):
        self.line.set_ydata(sensor_data["y"] + self.y_shift)
        self.graf.draw()
    
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
    t = threading.Thread(target=sensor_loop, daemon=True)
    t.start()

applikasjon = QApplication(sys.argv)
vindu = MainWindow()
vindu.show()
applikasjon.exec()