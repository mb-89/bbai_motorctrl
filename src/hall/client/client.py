from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtNetwork

import struct
import os.path as op
import time
from math import sin, pi

#import plugins here
from plugins.data import DataTree, DataTreeGuiPlugin
from plugins.plot import PlotGuiPlugin
from plugins.serverRC import ServerRCPlugin
from plugins.calc import CalcPlugin

class App(QtWidgets.QApplication):
    sampleSig = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__([])

        self.gui = Gui(self)

        #integrate plugins here
        self.plugins = {
            "data": DataTreeGuiPlugin(self),
            "calc": CalcPlugin(self),
            "plots": PlotGuiPlugin(self),
            "serverRC": ServerRCPlugin(self)
        }

        self.upstreamvars = self.plugins["data"].data.getUpstreamVarDict()
        self.downstreamvars = self.plugins["data"].data.getDownstreamVarDict()

        self.socket = QtNetwork.QUdpSocket()
        self.socket.bind(QtNetwork.QHostAddress(""), 6000)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.sample)

    def run(self):
        self.gui.start()
        for k,v in self.plugins.items(): v.start()
        self.socket.readyRead.connect(self.recvudp)
        self.timer.start()
        self.t0 = time.time()
        self.exec_()

    def recvudp(self):
        data = self.plugins["data"].data
        while self.socket.hasPendingDatagrams():
            data.recvUpstreamDatagram(self.socket)

    def sample(self):
        self.downstreamvars["sys.act.downstreamcnt"].value += 1
        #self.downstreamvars["sys.act.uptimeclient"].value = time.time()-self.t0

        #f = self.downstreamvars["test.sin.freq"].value
        #a = self.downstreamvars["test.sin.amp"].value
        #self.downstreamvars["test.sin.val"].value = sin(2*pi*f)*a

        self.sampleSig.emit()
        self.plugins["data"].data.sendDownstreamDatagram(self.socket)

    def __del__(self):
        self.socket.close()

class Gui(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.rootapp = app

        from client import client_ui
        self.ui = client_ui.Ui_ui()
        self.ui.setupUi(self)
        self.rootapp.setApplicationDisplayName("bbai.motorctrl.client")

    def start(self):
        #register shortcuts
        self.actions = {}
        for k,v in self.rootapp.plugins.items():
            acts = v.getActionDict()
            for actname, act in acts.items():
                self.actions[k+"."+actname] = self.createShortcut(*act)
        self.show()

    def createShortcut(self, fn, shortcut):
        action = QtWidgets.QAction(self)
        action.setShortcut(shortcut)
        action.triggered.connect(fn)
        self.addAction(action)
        return action

