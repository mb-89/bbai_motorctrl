from PyQt5 import QtCore
from PyQt5 import QtNetwork
from math import pi

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
        self.iPhaseOld = 0
        self.clkDiv = 0

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
        if self.downstreamvars["sys.ref.kill"].value: self.stopped.emit()
        self.upstreamvars["sys.act.upstreamcnt"].value += 1

        ael,amech = self.plugins["pru"].read(0,0,"ii",8)
        self.upstreamvars["motor.act.iAngleEl"].value = ael
        self.upstreamvars["motor.act.iAngleMech"].value = amech

        
        self.plugins["pru"].write([
            self.downstreamvars["motor.ref.iCtrlMode"].value,
            self.downstreamvars["motor.ref.iComPh"].value,
        ],0,8,"Ii",8)

        if self.clkDiv==4:
            self.iPhaseOld+=1
            if self.iPhaseOld>6:self.iPhaseOld-=6
            self.clkDiv = 0
        else:
            self.clkDiv+=1

        self.plugins["data"].data.sendUpstreamDatagram(self.socket)

    def recvudp(self):
        datatree = self.plugins["data"].data
        while self.socket.hasPendingDatagrams():
            datatree.recvDownstreamDatagram(self.socket)

    def __del__(self):
        self.socket.close()
