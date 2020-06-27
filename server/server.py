from PyQt5 import QtCore
from PyQt5 import QtNetwork

from plugins.log import Plugin as Plugin_log

class App(QtCore.QCoreApplication):

    def __init__(self):
        super().__init__([])
        self.isServer = True
        self.isClient = False
        self.running = False
        self.plugins = {"log":Plugin_log(self)}

        self.timer1sec = QtCore.QTimer()
        self.timer1sec.setInterval(1000)
        self.timer1sec.timeout.connect(self.sample1sec)

    def run(self):
        for k,v in self.plugins.items(): v.start()
        self.running = True
        self.timer1sec.start()
        self.exec_()

    def stop(self):
        if not self.running: return
        self.timer1sec.stop()
        self.running = False
        for k,v in self.plugins.items(): v.stop()
        self.quit()

    def sample1sec(self):
        #needed to catch ctrl+c
        self.plugins["log"].log.debug("bla1sec")

    def __del__(self):
        self.stop()

