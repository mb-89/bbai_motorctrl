from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtNetwork

import struct
import os.path as op

#import plugins here
from plugins.data import DataTree, DataTreeGuiPlugin

class App(QtWidgets.QApplication):
    def __init__(self):
        super().__init__([])

        self.gui = Gui(self)

        #integrate plugins here
        self.plugins = {
            "datatree": DataTreeGuiPlugin(self)
        }

        self.socket = QtNetwork.QUdpSocket()
        self.socket.bind(QtNetwork.QHostAddress(""), 6000)
        self.recvcnt = 0

    def run(self):
        self.gui.start()
        for k,v in self.plugins.items(): v.start()
        self.socket.readyRead.connect(self.recvudp)
        self.exec_()

    def recvudp(self):
        datatree = self.plugins["datatree"].data
        while self.socket.hasPendingDatagrams():
            datatree.readDatagram(self.socket)
        self.recvcnt+=1

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

