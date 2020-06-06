
from PyQt5 import QtCore, QtGui,QtWidgets
from PyQt5 import QtNetwork
import json
import struct
import os.path as op

DATA_ATTR = QtCore.Qt.UserRole
DATA_VALUEDISPLAY = DATA_ATTR+1
DATA_VALUEITEM = DATA_VALUEDISPLAY+1

class DataTree(QtCore.QObject):
    def __init__(self, definition):
        super().__init__()
        self._defpath = definition
        self._dict2qtModel(json.load(open(definition,"r")))

    def _dict2qtModel(self, dct, _parent = None):
        if _parent is None:
            self.mdl = QtGui.QStandardItemModel()
            self.mdl.setHorizontalHeaderLabels(["Var","Val"])
            self.mdl.setColumnCount(2)
            self.upstreamVars = []
            self.downstreamVars = []
            self.vardict = {}
            root = self.mdl.invisibleRootItem()
            target = root
            target.parentObj = None
        else:
            target = _parent

        for k,v in dct.items():
            isLeaf = any((x.startswith("_") for x in v))
            qtItem = QtGui.QStandardItem(k)
            qtItem.parentObj = target
            if isLeaf:
                streamdir = v.get("stream_dir")
                if streamdir == "up":     self.upstreamVars.append(qtItem)
                elif streamdir == "down": self.downstreamVars.append(qtItem)
                qtItem.value = 0
                valstr = str(qtItem.value)
                valueDisplay = QtGui.QStandardItem(valstr)
                valueDisplay.oldText = valstr
                qtItem.setData(v, DATA_ATTR)
                qtItem.setData(qtItem, DATA_VALUEITEM)
                valueDisplay.setData(qtItem, DATA_VALUEITEM)
                qtItem.setData(valueDisplay, DATA_VALUEDISPLAY)
                target.appendRow([qtItem, valueDisplay])
                self.vardict[".".join(self.getFullName(qtItem))] = qtItem
            else:
                target.appendRow(qtItem)
                self._dict2qtModel(v,qtItem)

        if _parent is None:
            self.upstreamFmt = "".join((x.data(DATA_ATTR)["_type"] for x in self.upstreamVars))
            self.upstreamLen = struct.calcsize(self.upstreamFmt)
            self.downstreamFmt = "".join((x.data(DATA_ATTR)["_type"] for x in self.downstreamVars))
            self.downstreamLen = struct.calcsize(self.downstreamFmt)

    def recvUpstreamDatagram(self, sock):
        rawData = sock.readDatagram(self.upstreamLen)
        data = struct.unpack(self.upstreamFmt,rawData[0])
        for newval, var in zip(data, self.upstreamVars):var.value = newval

    def recvDownstreamDatagram(self, sock):
        rawData = sock.readDatagram(self.downstreamLen)
        data = struct.unpack(self.downstreamFmt,rawData[0])
        for newval, var in zip(data, self.downstreamVars):var.value = newval

    def sendUpstreamDatagram(self, sock):
        data = struct.pack(self.upstreamFmt,*(x.value for x in self.upstreamVars))
        sock.writeDatagram(data, QtNetwork.QHostAddress.Broadcast, 6000)

    def sendDownstreamDatagram(self, sock):
        data = struct.pack(self.downstreamFmt,*(x.value for x in self.downstreamVars))
        sock.writeDatagram(data, QtNetwork.QHostAddress.Broadcast, 6001)

    def getUpstreamVarDict(self):
        dct = {}
        for x in self.upstreamVars:
            dct[".".join(self.getFullName(x))] = x
        return dct

    def getDownstreamVarDict(self):
        dct = {}
        for x in self.downstreamVars:
            dct[".".join(self.getFullName(x))] = x
        return dct

    def getFullName(self, x):
        if x.parentObj is None:
            return []
        else:
            pn = self.getFullName(x.parentObj)
            pn.append(x.text())
            return pn

    def syncQtVals(self):
        for x in self.upstreamVars:
            vd = x.data(DATA_VALUEDISPLAY)
            vd.setText(str(x.value))
        for x in self.downstreamVars:
            vd = x.data(DATA_VALUEDISPLAY)
            newstr = str(x.value)
            oldstr = vd.oldText
            currstr = vd.text()
            #if the value was overridden by the user (via the text), use the text as new value
            if currstr != oldstr:
                x.value = int(currstr) #TODO: proper casting
                vd.oldText = currstr
            #if the value has changed (bc a part of the program modified it), update the value display
            elif newstr != currstr:
                vd.setText(newstr)
                x.value = int(vd.text()) #TODO: proper casting
                vd.oldText = newstr

class DataTreeServerPlugin():
    def __init__(self, rootapp): 
        self.rootapp = rootapp
        self.data = DataTree(op.join(op.dirname(__file__),"data.json"))

    def start(self):
        for x in self.data.upstreamVars:x.value = 0
        for x in self.data.downstreamVars:x.value = 0
    def stop(self):pass

class DataTreeGuiPlugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        self.data = DataTree(op.join(op.dirname(__file__),"data.json"))
        self.widget = Widget(self, rootapp)
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.setInterval(1000)
        self.updateTimer.timeout.connect(self.data.syncQtVals)

    def getActionDict(self):
        return {"toggleDataTree" : (self.widget.togglehide, "Ctrl+l")}
    
    def start(self):
        self.updateTimer.start()
        for x in self.data.upstreamVars:x.value = 0
        for x in self.data.downstreamVars:x.value = 0

class Widget(QtWidgets.QDockWidget):
    def __init__(self, parent, app):
        super().__init__(app.gui)
        self.rootapp = app
        self.rootplugin = parent
        self.setWindowTitle("Data")
        self.resize(600,400)
        app.gui.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.rootplugin.data.mdl)
        self.setWidget(self.tree)

    def togglehide(self):
        self.setVisible(self.isHidden())