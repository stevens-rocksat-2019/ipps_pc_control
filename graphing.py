from multiprocessing import Queue

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import sys


class CurvePlotter:
    def __init__(self, curve):
        self.data = np.empty(100)
        self.ptr = 0
        self.curve = curve

    def add_point(self, data):
        self.data[self.ptr] = data
        self.ptr += 1
        if self.ptr >= self.data.shape[0]:
            tmp = self.data
            self.data = np.empty(self.data.shape[0] * 2)
            self.data[:tmp.shape[0]] = tmp
        self.curve.setData(self.data[:self.ptr])
        self.curve.setPos(-self.ptr, 0)


class ToggleButton(QtGui.QWidget):
    def __init__(self, label, callback=lambda x: None, description=None):
        super(ToggleButton, self).__init__()

        self.callback = callback

        label = QtGui.QLabel(label)
        btn = QtGui.QPushButton("on")
        btn2 = QtGui.QPushButton("off")

        btn.clicked.connect(self.on_clicked)
        btn2.clicked.connect(self.off_clicked)
        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(label)
        layout.addStretch(1)
        if description is not None:
            layout.addWidget(QtGui.QLabel(description))
        layout.addWidget(btn)
        layout.addWidget(btn2)

    def on_clicked(self):
        self.callback(True)

    def off_clicked(self):
        self.callback(False)


class ButtonSet(QtGui.QWidget):
    def __init__(self, command_callback):
        super(ButtonSet, self).__init__()

        self.common_callback = command_callback
        layout = QtGui.QVBoxLayout()
        layout.addWidget(ToggleButton("Global", description="Everything", callback=lambda x: self.common_callback(0, x)))
        layout.addWidget(ToggleButton("1: Vibe Iso Control ", description="5V @ 1.5A", callback=lambda x: self.common_callback(1, x)))
        layout.addWidget(ToggleButton("2: Soldering Control", description="5V @ 1.5A", callback=lambda x: self.common_callback(2, x)))
        layout.addWidget(ToggleButton("3: Pressure Sensor (reserve)", description="5V @ 1.5A", callback=lambda x: self.common_callback(3, x)))
        layout.addWidget(ToggleButton("4: Soldering Heater", description="12V @ 6+ A", callback=lambda x: self.common_callback(4, x)))
        layout.addWidget(ToggleButton("5: Soldering Fan", description="12V @ 1A", callback=lambda x: self.common_callback(5, x)))
        layout.addWidget(ToggleButton("6: Pressure Sensor Main", description="12V @ 1A", callback=lambda x: self.common_callback(6, x)))
        layout.addWidget(ToggleButton("7: Pressure Sensor Sensor", description="36V @ 0.25A", callback=lambda x: self.common_callback(7, x)))
        self.setLayout(layout)

    def common_callback(self, rail, state):
        self.command_callback(rail, state)


class GraphWindow:

    def __init__(self, command_callback):
        self.win = pg.GraphicsWindow()
        self.win.setWindowTitle('RockSAT Power Supply Data Viewer')

        # 2) Allow data to accumulate. In these examples, the array doubles in length
        #    whenever it is full.
        self.p1 = self.win.addPlot(title="Voltages")
        self.p2 = self.win.addPlot(title="Currents")
        self.p4 = self.win.addPlot(title="Temperature and Humidity")

        # Use automatic downsampling and clipping to reduce the drawing load
        self.p1.setDownsampling(mode='peak')
        self.p1.setClipToView(True)
        self.p1.setRange(xRange=[-100, 0])

        self.p2.setDownsampling(mode='peak')
        self.p2.setClipToView(True)
        self.p2.setRange(xRange=[-100, 0])

        self.p4.setDownsampling(mode='peak')
        self.p4.setClipToView(True)
        self.p4.setRange(xRange=[-100, 0])

        colors = ["b", "g", "r", "c", "m", "y", "w", (0.5, 0.5, 0.5, 1.0)]  #"bgrcmywk"

        self.volt_curves = [CurvePlotter(self.p1.plot(pen=c)) for c in colors]
        self.curr_curves = [CurvePlotter(self.p2.plot(pen=c)) for c in colors]
        self.temp_hum_curves = [CurvePlotter(self.p4.plot(pen=c)) for c in colors[0:2]]

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.data_poll)
        self.timer.start(1)

        proxy = QtGui.QGraphicsProxyWidget()
        # button = QtGui.QPushButton('button')
        # button = ToggleButton("Supply 1", lambda x: print("ps1", x), description="Pressure Sensor 5V")
        button = ButtonSet(command_callback)
        proxy.setWidget(button)

        self.p3 = self.win.addLayout(row=1, col=0)
        self.p3.addItem(proxy, row=1, col=1)

        self.queue = Queue()

    def data_poll(self):
        if not self.queue.empty():
            voltages, currents, temp_hum = self.queue.get_nowait()
            for n, i in enumerate(voltages):
                if n == 0:
                    continue

                self.volt_curves[n].add_point(i)

            for n, i in enumerate(currents):
                self.curr_curves[n].add_point(i)

            if temp_hum is not None:
                for n, i in enumerate(temp_hum):
                    self.temp_hum_curves[n].add_point(i)

        else:
            pass
            # print("data poll no point")

    def add_data(self, data):
        self.queue.put(data)

    @staticmethod
    def event_loop():
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()


#
# ## Start Qt event loop unless running in interactive mode or using pyside.
# if __name__ == '__main__':
#     import sys
#     if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#         QtGui.QApplication.instance().exec_()
#

if __name__ == '__main__':
    g = GraphWindow()
    g.event_loop()

