from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtNetwork

import os.path as op

from plugins.log import Plugin as Plugin_log
from plugins.serverRC import Plugin as Plugin_serverRC

class App(QtWidgets.QApplication):
    def __init__(self):
        super().__init__([])
        self.gui = Gui(self)
        self.isServer = False
        self.isClient = True
        self.plugins = {
            "log":Plugin_log(self),
            "serverRC":Plugin_serverRC(self)
            }
        self.running = False
        self.aboutToQuit.connect(self.stop)

    def run(self):
        self.gui.start()
        for k,v in self.plugins.items(): v.start()
        self.running = True
        self.exec_()

    def stop(self):
        if not self.running: return
        self.running = False
        for k,v in self.plugins.items(): v.stop()
        self.quit()

    def __del__(self):
        self.stop()

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
                self.actions[k+"."+actname] = self.registerAction(*act)
        self.show()

    def registerAction(self, fn, shortcut = None, menuEntry = None, ToolbarEntry = None):
        action = QtWidgets.QAction(self)
        action.triggered.connect(fn)
        self.addAction(action)

        if shortcut: action.setShortcut(shortcut)

        return action

