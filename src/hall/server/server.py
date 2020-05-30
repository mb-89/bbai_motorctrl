from PyQt5 import QtCore
from PyQt5 import QtNetwork

#import plugins here
from plugins.bbai_GPIO import GPIOplugin
from plugins.data import DataTreeServerPlugin

class App(QtCore.QCoreApplication):
    def __init__(self):
        super().__init__([])

        #integrate plugins here
        self.plugins = {
            "GPIO": GPIOplugin(self),
            "data": DataTreeServerPlugin(self)
        }

        self.GPIOs = {
            "H1": self.plugins["GPIO"].getPinHandler(header=8, pin=12),
            "H2": self.plugins["GPIO"].getPinHandler(header=8, pin=11),
            "H3": self.plugins["GPIO"].getPinHandler(header=8, pin=18)
        }

        self.upstreamvars = self.plugins["data"].data.getUpstreamVarDict()

        self.socket = QtNetwork.QUdpSocket()
        self.socket.bind(QtNetwork.QHostAddress(""), 6001)

        self.samplecnt = 0
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.sample)

    def run(self):
        for k,v in self.plugins.items(): v.start()
        self.socket.readyRead.connect(self.recvudp)
        self.timer.start()
        self.exec_()

    def sample(self):
        self.upstreamvars["motor.act.hall0"].value = self.GPIOs["H1"].read()
        self.upstreamvars["motor.act.hall1"].value = self.GPIOs["H2"].read()
        self.upstreamvars["motor.act.hall2"].value = self.GPIOs["H3"].read()

        if self.downstreamVars["sys.ref.kill"].value: self.quit()

        self.upstreamvars["sys.act.upstreamcnt"].value += 1

        self.plugins["data"].data.sendUpstreamDatagram(self.socket)

    def recvudp(self):
        datatree = self.plugins["data"].data
        while self.socket.hasPendingDatagrams():
            datatree.recvDownstreamDatagram(self.socket)


    def __del__(self):
        self.socket.close()
