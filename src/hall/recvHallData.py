from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtNetwork
import struct
import pyqtgraph as pg
from collections import deque

def main():
    app = App()
    app.start()

POLES = 16
POLEPAIRS = 8

class App(QtGui.QApplication):
    def __init__(self):
        super().__init__([])

        self.socket = QtNetwork.QUdpSocket()
        self.socket.bind(QtNetwork.QHostAddress(""), 6000)
        self.readcnt = 0

        self.t1 = QtCore.QTimer()
        self.t1.setInterval(15)
        self.t1.timeout.connect(self.sample)

        self.seg = 0
        self.h1 = 0
        self.h2 = 0
        self.h3 = 0
        self.pos = 0

        self.win = pg.GraphicsWindow()
        self.plt1 = self.win.addPlot(row=0,col=0)
        self.plt2 = self.win.addPlot(row=1,col=0)
        proxy = QtGui.QGraphicsProxyWidget()
        checkbox = QtWidgets.QCheckBox("update")
        checkbox.setChecked(True)
        proxy.setWidget(checkbox)
        self.win.addItem(proxy, row=2,col=0)
        self.plotUpdates = checkbox
        self.plt1data1 = deque([0]*1000,1000)
        self.plt1data2 = deque([0]*1000,1000)
        self.plt1data3 = deque([0]*1000,1000)
        self.plt2data1 = deque([0]*1000,1000)
        self.plt1curve1 = self.plt1.plot(self.plt1data1,pen="r")
        self.plt1curve2 = self.plt1.plot(self.plt1data1,pen="g")
        self.plt1curve3 = self.plt1.plot(self.plt1data1,pen="b")

        self.plt2curve1 = self.plt2.plot(self.plt2data1)
        self.win.setWindowTitle('Hall sensor position data')
        self.win.show()

    def start(self):
        self.socket.readyRead.connect(self.recvudp)
        self.t1.start()
        self.exec_()

    def recvudp(self):
        newvals = []
        while self.socket.hasPendingDatagrams():
            data = self.socket.readDatagram(1024)
            datalen = int(len(data[0])/4)
            newvals.extend(struct.unpack(f"{datalen}f",data[0]))
        self.readcnt+=1
        if (self.readcnt % 100)==0:
            print(self.readcnt, newvals)

        self.plt1data1.append(newvals[0]*0.9)
        self.plt1data2.append(1+newvals[1]*0.9)
        self.plt1data3.append(2+newvals[2]*0.9)

        self.calcpos(*newvals[-3:])

    def calcpos(self, h1,h2,h3):
        self.h1 = h1
        self.h2 = h2
        self.h3 = h3

        seg = -1
        sum = h1+h2+h3
        
        if sum == 1:
            if h3:      seg = 0
            elif h2:    seg = 4
            elif h1:    seg = 2
        else: #sum=2
            if not h3:  seg = 3
            elif not h2:seg = 1
            elif not h1:seg = 5

        segwidth = 360/6/POLEPAIRS
        if seg <0:return#sensor error
        if (seg>self.seg) or (seg==0 and self.seg==5) : self.pos += segwidth
        if (seg<self.seg) or (seg==5 and self.seg==0) : self.pos -= segwidth
        self.seg = seg

        self.plt2data1.append(self.pos)



    def sample(self):
        if self.plotUpdates.isChecked():
            self.plt1curve1.setData(self.plt1data1)
            self.plt1curve2.setData(self.plt1data2)
            self.plt1curve3.setData(self.plt1data3)
            self.plt2curve1.setData(self.plt2data1)

    def __del__(self):
        self.socket.close()

if __name__ == "__main__":main()