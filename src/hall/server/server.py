from PyQt5 import QtCore

#import plugins here
from plugins.bbai_GPIO import GPIOplugin

class App(QtCore.QCoreApplication):
    def __init__(self):
        super().__init__([])

        #integrate plugins here
        self.plugins = {
            "GPIO": GPIOplugin(self)
        }

        self.GPIOs = {
            "H1": self.plugins["GPIO"].getPinHandler(header=8, pin=12),
            "H2": self.plugins["GPIO"].getPinHandler(header=8, pin=11),
            "H3": self.plugins["GPIO"].getPinHandler(header=8, pin=18)
        }

    def run(self):
        for k,v in self.plugins.items(): v.start()

        self.cnt = 0
        self.slowTimer = QtCore.QTimer()
        self.slowTimer.setInterval(10)
        self.slowTimer.timeout.connect(self.sampleSlow)
        self.slowTimer.start()

        self.exec_()

    def sampleSlow(self):
        data = (self.GPIOs["H1"].read(), self.GPIOs["H2"].read(), self.GPIOs["H3"].read())
        self.cnt+=1
        if self.cnt%100 == 0:
            print(data)

        pass # we only need this to catch ctrc-c
