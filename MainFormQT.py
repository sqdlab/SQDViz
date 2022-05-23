from PySide6 import QtWidgets, QtCore
from PySide6.QtUiTools import QUiLoader
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np

class MainWindow:
    def __init__(self, win, pltWidget):
        self.graphWidget = pltWidget
        # win.setCentralWidget(self.graphWidget)

        hour = [1,2,3,4,5,6,7,8,9,10]
        temperature = [30,32,34,32,33,31,29,32,35,45]

        # plot data: x, y values
        self.data_line = self.graphWidget.plot(hour, temperature)
        # ... init continued ...
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        win.btn_test.clicked.connect(self.event_btn_OK)

    def event_btn_OK(self):
        print('noice')

    def update_plot_data(self):
        xVals = np.arange(0,10,0.1)
        yVals = np.sin(xVals) + 0.1*np.random.rand(xVals.size)

        self.data_line.setData(xVals, yVals)  # Update the data.


class UiLoader(QUiLoader):
    def createWidget(self, className, parent=None, name=""):
        if className == "PlotWidget":
            self.plot_widget = pg.PlotWidget(parent=parent)
            return self.plot_widget
        return super().createWidget(className, parent, name)

def mainwindow_setup(w):
    w.setWindowTitle("MainWindow Title")

def main():
    loader = UiLoader()
    app = QtWidgets.QApplication(sys.argv)
    window = loader.load("main.ui", None)
    main_win = MainWindow(window, loader.plot_widget)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
