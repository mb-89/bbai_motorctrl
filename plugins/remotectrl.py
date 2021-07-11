import logging
import sys
from PyQt5 import  QtWidgets, QtCore
import paramiko
import os.path as op
import os
import time

log = None
MULTITHREAD = True

class Plugin():
    def __init__(self, rootapp):
        global log
        self.rootapp = rootapp
        log = self.rootapp.log
        if self.rootapp.isServer:
            log.error("Plugin 'remotectrl' is not compatible to server-side and will be skipped.")
            return
        self.connected = False
        self.widget = SSHWidget(rootapp)
        self.proc = QtCore.QProcess()
        
        self.proc.readyReadStandardError.connect(self.readstderr)
        self.proc.readyReadStandardOutput.connect(self.readstdout)

    def start(self):
        self.startProc()
    def stop(self):pass
    def getActionDict(self):return {"sshterm": (self.widget.togglehide, f"Ctrl+^")}
    def __del__(self): self.stop()

    def changeConStatus(self, con):
        self.connected = con
        log.info(f"SSH connection state changed to <{'connected' if con else 'disconnected'}>")

    def startProc(self):
        self.proc.start("ssh", ["-Tt", "-o", "ConnectTimeout=2", "root@192.168.0.20"])

    def readstdout(self):
        data = bytes(self.proc.readAllStandardOutput()).decode("cp850").strip()
        if self.connected:
            print(f"stdout:{data}")
        elif data.startswith("root@192.168.0.20's password:"):
            self.proc.write("bbai")
        else:
            bla = 1


    def readstderr(self):
        data = bytes(self.proc.readAllStandardError()).decode("cp850").strip()
        if not self.connected:
            if data.startswith("Pseudo-terminal"):
                self.proc.write(b"bbai")
        print(f"stderr:{data}")

class SSHWidget(QtWidgets.QDockWidget):
    closed = QtCore.pyqtSignal()
    def __init__(self, app):
        super().__init__()
        self.rootapp = app
        ui = app.gui.ui
        self.console = SSHConsole()
        self.setHidden(True)
        self.setWidget(self.console)
        self.rootapp.gui.addDockWidget(QtCore.Qt.TopDockWidgetArea, self)
        self.resize(600,400)
        self.setWindowTitle('bbai_motorctrl ssh terminal')

    def togglehide(self):
        self.setVisible(self.isHidden())

class SSHConsole(QtWidgets.QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setMaximumBlockCount(100)

    def keyPressEvent(self, e):
        pass

    def mousePressEvent(self, e): self.setFocus()
    def mouseDoubleClickEvent(self, e): pass
    def contextMenuEvent(self, e): pass