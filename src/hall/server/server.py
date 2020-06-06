from PyQt5 import QtCore
from PyQt5 import QtNetwork

#import plugins here
from plugins.bbai_GPIO import GPIOplugin
from plugins.data import DataTreeServerPlugin
from plugins.pru import PRUPlugin

class App(QtCore.QCoreApplication):
    stopped = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__([])

        #integrate plugins here
        self.plugins = {
            "data": DataTreeServerPlugin(self),
            "pru": PRUPlugin(self)
        }

        self.upstreamvars = self.plugins["data"].data.getUpstreamVarDict()
        self.downstreamvars = self.plugins["data"].data.getDownstreamVarDict()

        self.socket = QtNetwork.QUdpSocket()
        self.socket.bind(QtNetwork.QHostAddress(""), 6001)

        self.samplecnt = 0
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.sample)

    def run(self):
        for k,v in self.plugins.items(): v.start()
        self.socket.readyRead.connect(self.recvudp)
        self.stopped.connect(self.stop)
        self.timer.start()
        self.exec_()

    def stop(self):
        self.timer.stop()
        self.socket.close()
        for k,v in self.plugins.items(): v.stop()
        self.quit()

    def sample(self):
        #self.upstreamvars["motor.act.hall0"].value = self.GPIOs["H1"].read()
        #self.upstreamvars["motor.act.hall1"].value = self.GPIOs["H2"].read()
        #self.upstreamvars["motor.act.hall2"].value = self.GPIOs["H3"].read()

        if self.downstreamvars["sys.ref.kill"].value: self.stopped.emit()

        self.upstreamvars["sys.act.upstreamcnt"].value += 1
        tmp0,tmp1 = self.plugins["pru"].read(0,0,"II",8)

        self.upstreamvars["motor.act.commutations"].value = tmp0
        self.upstreamvars["motor.act.iPos"].value = tmp1

        self.plugins["data"].data.sendUpstreamDatagram(self.socket)

    def recvudp(self):
        datatree = self.plugins["data"].data
        while self.socket.hasPendingDatagrams():
            datatree.recvDownstreamDatagram(self.socket)


    def __del__(self):
        self.socket.close()
