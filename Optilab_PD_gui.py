# -*- coding: utf-8 -*-

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.console
import numpy as np

import Optilab_PD as pd

from pyqtgraph.dockarea import *
from functools import partial
import serial.tools.list_ports

app = QtGui.QApplication([])
win = QtGui.QMainWindow()
area = DockArea()
win.setCentralWidget(area)
win.resize(1000,600)
win.setWindowTitle(r'Optilab PD control')

## Create docks, place them into the window one at a time.
## Note that size arguments are only a suggestion; docks will still have to
## fill the entire dock area and obey the limits of their internal widgets.
d1 = Dock("PD control", size=(300, 100))     ## give this dock the minimum possible size
d2 = Dock("Console", size=(100,300), closable=True)
d3 = Dock("COM", size=(100,20))
d4 = Dock("Plot of the last 100 read values", size=(100,100))

area.addDock(d1, 'left')      ## place d1 at left edge of dock area (it will fill the whole space since there are no other docks yet)
area.addDock(d2, 'right')     ## place d2 at right edge of dock area
area.addDock(d3, 'bottom', d1)## place d3 at bottom edge of d1
area.addDock(d4, 'bottom', d1)

# Instance of PD connection
com = None

def PD_disconnect():
    if com is None:
        w2.append("<font color='red'><strong>Not connected</strong></font>")
        return
    w2.append("<font color='black'><strong>Disconnecting PD</strong></font>")
    com.disconnect()

def PD_connect():
    global com, port_list, w2
    port = str(port_list.currentText().split(" ")[-1][1:-1])
    baudrate=9600
    com = pd.OptiLabPD(port=port, baudrate=baudrate)
    if com is not None:
        w2.append("<font color='blue'><strong>Established connection at port {0} with a baudrate of {1}</strong></font>".format(port, baudrate))
    else:
        w2.append("<font color='red'><strong>Failed to establish connection at port {0} with a baudrate of {1}</strong></font>".format(port, baudrate))
        
in_pow = []

def update_values():
    global com, in_pow
    if com is None or not com.pd.isOpen():
        return
    # Issue a read
    status = com.get_status()
    # Update GUI
    pd_input.setText("Input [dBm]: {:.2f}".format(status[3]))   
    pd_temperature.setText("Temperature [deg C]: {:.2f}".format(status[0]))
    pd_v8.setText("Voltage (8V): {:.2f}".format(status[1]))
    pd_v12.setText("Voltage (12V): {:.2f}".format(status[2]))
    if status[4] is True:
        pd_alarm.setText("<h1><font color='red'>POWER HIGH</font><h1>")
    else:
        pd_alarm.setText("<h1><font color='green'>POWER OK</font><h1>")
  
    # Plot acquired values, pick last 100.
    if len(in_pow) > 100:
        in_pow = in_pow[1:]
        
    in_pow.append(status[3])
    
    p1.plot(np.array(in_pow), clear=True)


## Stuff that belongs to Dock d1 inside a Layout
pd_layout = pg.LayoutWidget()

pd_input = QtGui.QLabel("Input [dBm]:")
pd_temperature = QtGui.QLabel("Temperature [deg C]:")
pd_v8 = QtGui.QLabel("Voltage (8V) :")
pd_v12 = QtGui.QLabel("Voltage (12V) :")
pd_alarm = QtGui.QLabel("Power alarm")

pd_layout.addWidget(pd_input, row=0, col=0)

pd_layout.addWidget(pd_temperature, row=1, col=0)
pd_layout.addWidget(pd_v8, row=2, col=0)
pd_layout.addWidget(pd_v12, row=3, col=0)
pd_layout.addWidget(pd_alarm, row=4, col=0)


w1 = pg.LayoutWidget()

w1.addWidget(pd_layout)

# Push to d1
d1.addWidget(w1)

## Stuff that belongs to Dock d4 (Plots)
p1 = pg.PlotWidget(title="Input power [dBm]")

p1.enableAutoRange()

d4.addWidget(p1)


## Stuff that belong to Dock d2 (Console)
w2 = QtGui.QTextEdit()
d2.addWidget(w2)

## Stuff that belongs to Dock d3 (Port connection)
port_label = QtGui.QLabel("Port:")
port_list = QtGui.QComboBox()
port_connect = QtGui.QPushButton()
port_connect.setText("Connect")

port_disconnect = QtGui.QPushButton()
port_disconnect.setText("Disconnect")

port_layout = pg.LayoutWidget()
port_layout.addWidget(port_label, row=0, col=0)
port_layout.addWidget(port_list, row=0, col=1)
port_layout.addWidget(port_connect, row=0, col=2)
port_layout.addWidget(port_disconnect, row=0, col=3)

port_connect.clicked.connect(PD_connect)
port_disconnect.clicked.connect(PD_disconnect)

# Populate port list:
for port_address, port_name, _ in list(serial.tools.list_ports.comports())[::-1]:
    port_list.addItem("{0} ({1})".format(port_name, port_address))
d3.addWidget(port_layout)

win.show()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    
    refresh_timer = QtCore.QTimer()
    refresh_timer.timeout.connect(update_values)
    refresh_timer.start(1500)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
 