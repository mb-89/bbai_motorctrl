
from PyQt5 import QtCore, QtGui,QtWidgets
from PyQt5 import QtNetwork
import json
import struct
import os.path as op

DATA_ATTR = QtCore.Qt.UserRole

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
            self.downstreamvars = []
            root = self.mdl.invisibleRootItem()
            target = root
            target.parentObj = None
        else:
            target = _parent

        for k,v in dct.items():
            isLeaf = any((x.startswith("_") for x in v))
            qtItem = QtGui.QStandardItem(k)
            if isLeaf:
                streamdir = v.get("stream_dir")
                if streamdir == "up":     self.upstreamVars.append(qtItem)
                elif streamdir == "down": self.downstreamvars.append(qtItem)
                qtItem.setData(v, DATA_ATTR)
                qtItem.value = 0
            qtItem.parentObj = target
            target.appendRow(qtItem)
            if not isLeaf: 
                self._dict2qtModel(v,qtItem)

        self.upstreamFmt = "".join((x.data(DATA_ATTR)["_type"] for x in self.upstreamVars))
        self.upstreamLen = struct.calcsize(self.upstreamFmt)
        self.downstreamFmt = "".join((x.data(DATA_ATTR)["_type"] for x in self.downstreamvars))
        self.downstreamLen = struct.calcsize(self.downstreamFmt)

    def recvUpstreamDatagram(self, sock):
        rawData = sock.readDatagram(self.upstreamlen)
        data = struct.unpack(self.upstreamFmt,rawData[0])

    def sendUpstreamDatagram(self, sock):
        data = struct.pack(self.upstreamFmt,*(x.value for x in self.upstreamVars))
        sock.writeDatagram(data, QtNetwork.QHostAddress.Broadcast, 6000)

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

class DataTreeServerPlugin():
    def __init__(self, rootapp): 
        self.rootapp = rootapp
        self.data = DataTree(op.join(op.dirname(__file__),"data.json"))

    def start(self):pass

class DataTreeGuiPlugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        self.data = DataTree(op.join(op.dirname(__file__),"data.json"))
        self.widget = Widget(self, rootapp)

    def getActionDict(self):
        return {"toggleDataTree" : (self.widget.togglehide, "Ctrl+l")}
    
    def start(self):pass

class Widget(QtWidgets.QDockWidget):
    def __init__(self, parent, app):
        super().__init__(app.gui)
        self.rootapp = app
        self.rootplugin = parent
        self.setWindowTitle("Datatree")
        self.resize(600,400)
        app.gui.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.rootplugin.data.mdl)
        self.setWidget(self.tree)

    def togglehide(self):
        self.setVisible(self.isHidden())