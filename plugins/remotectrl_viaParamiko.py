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
        self.ssh = SSHcon(rootapp,self)
        self.console = SSHConsole(rootapp)

    def start(self):
        self.ssh.start()
    def stop(self):
        self.ssh.stop()
    def getActionDict(self):return {"sshterm": (self.console.togglehide, f"Ctrl+^")}
    def __del__(self): self.stop()

    def changeConStatus(self, con):
        self.connected = con
        log.info(f"SSH connection state changed to <{'connected' if con else 'disconnected'}>")
        self.console.lw.clear()
        if not con:
            self.console.lw.putData("***not connected***")

class SSHcon(QtCore.QObject):
    stopSig = QtCore.pyqtSignal()
    def __init__(self, rootapp, rootplugin):
        super().__init__()
        self.rootapp = rootapp
        self.rootplugin = rootplugin
        self.con = None
    def start(self):
        if self.con: return

        self.conThread = QtCore.QThread()
        self.con = SSHconWorker(self)
        if MULTITHREAD: self.con.moveToThread(self.conThread)
        self.conThread.started.connect(self.con.run)
        self.con.done.connect(lambda: self.stop(1))
        self.con.connectionStatusChanged.connect(self.rootplugin.changeConStatus)
        self.con.recv.connect(self.rootplugin.console.lw.putData)
        self.stopSig.connect(self.con.stop)
        self.rootplugin.console.lw.getData.connect(self.send)
        self.conThread.start()

    def send(self, data):
        if not self.con: return
        self.con.send(data)

    def stop(self, _ret = None):
        if not _ret:
            self.stopSig.emit()
            return
        self.conThread.quit()
        self.con = None

class SSHconWorker(QtCore.QObject):
    done = QtCore.pyqtSignal()
    recv = QtCore.pyqtSignal(str)
    connectionStatusChanged = QtCore.pyqtSignal(bool)
    def __init__(self,parent):
        super().__init__()
        self.parentElem = parent
    def run(self):
        self.running = True
        self.connected = False
        while self.running:
            if not self.connected:#establish connection
                try:
                    self.con = paramiko.SSHClient()
                    self.con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    self.con.connect("192.168.0.20", username="root", password="bbai", timeout =2)#yeah i know.
                    self.chan = self.con.get_transport().open_session()
                    self.chan.get_pty()
                    self.chan.invoke_shell()
                    self.chan.settimeout(2)
                    self.connected = True
                    self.connectionStatusChanged.emit(True)
                except:
                    pass
                continue
            #if we are here, the connection is ok:
            try:
                data = self.chan.recv(256).decode("ascii")
                self.recv.emit(data)
                if data == "":
                    self.connected = False
                    self.con.close()
                    self.connectionStatusChanged.emit(False)
            except Exception as e: #try a pwd cmd
                print(repr(e))
                try: self.con.exec_command('pwd', timeout=5)
                except Exception as e:
                    print(repr(e))
                    self.connected = False
                    self.con.close()
                    self.connectionStatusChanged.emit(False)

        self.done.emit()
    def stop(self):
        self.running = False

    @QtCore.pyqtSlot(str)
    def send(self, data):
        if not self.connected:return
        self.chan.send(data)

class SSHConsole(QtWidgets.QDockWidget):
    closed = QtCore.pyqtSignal()
    def __init__(self, app):
        super().__init__()
        self.rootapp = app
        ui = app.gui.ui
        self.lw = PlainTextConsole()
        self.setHidden(True)
        self.setWidget(self.lw)
        self.rootapp.gui.addDockWidget(QtCore.Qt.TopDockWidgetArea, self)
        self.resize(600,400)
        self.setWindowTitle('bbai_motorctrl ssh terminal')

    def togglehide(self):
        self.setVisible(self.isHidden())

class PlainTextConsole(QtWidgets.QPlainTextEdit):
    getData = QtCore.pyqtSignal(str)
    ignorelst = []
    localEchoEnabled = False

    def __init__(self):
        super().__init__()
        self.setMaximumBlockCount(100)

    def putData(self, data):
        self.insertPlainText(data)
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def setLocalEchoEnabled(self, set):
        self.localEchoEnabled = set

    def keyPressEvent(self, e):
        if e.key() in self.ignorelst:return
        if self.localEchoEnabled: super().keyPressEvent(e)
        self.getData.emit(e.text())

    def mousePressEvent(self, e): self.setFocus()
    def mouseDoubleClickEvent(self, e): pass
    def contextMenuEvent(self, e): pass