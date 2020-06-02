
from PyQt5 import QtCore, QtGui,QtWidgets
from PyQt5 import QtNetwork
import json
import struct
import os.path as op
import pyqtgraph as pg
from .data import DATA_VALUEITEM
from collections import deque

class PlotGuiPlugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        self.widgets = {}
        self.buffers = {}
        for idx in range(9):
            self.widgets[f"P{idx+1}"] = Widget(self, rootapp, idx+1)
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.sample)

    def getActionDict(self):
        dct = {}
        for idx in range(9):
            nr = idx+1
            dct[f"toggleP{nr}"] = (self.widgets[f"P{nr}"].togglehide, f"{nr}")
            dct[f"addTrace2P{nr}"] = (self.widgets[f"P{nr}"].addTraces, f"Ctrl+{nr}")
        return dct
    
    def start(self):
        self.rootapp.sampleSig.connect(self.updateBuffers)
        self.timer.start()

    def updateBuffers(self):
        for k,v in self.buffers.items():
            v.update()

    def sample(self):
        for widname, wid in self.widgets.items():
            for k,v in wid.traces.items():
                plt = v
                data = self.buffers[k]._buf
                plt.setData(data)


class Widget(QtWidgets.QDockWidget):
    def __init__(self, parent, app, nr):
        super().__init__(app.gui)
        self.rootapp = app
        self.nr = nr
        self.rootplugin = parent
        self.setWindowTitle(f"Plot group #{nr}")
        self.resize(800,600)
        app.gui.addDockWidget(QtCore.Qt.TopDockWidgetArea, self)
        self.setFloating(True)
        self.setHidden(True)
        self.traces = {}

        w = QtWidgets.QWidget()
        l =  QtWidgets.QVBoxLayout(); l.setSpacing(0); l.setContentsMargins(0,0,0,0)
        w.setLayout(l)

        self.traceList = QtWidgets.QTreeView()
        self.traceList.setMaximumHeight(200)
        self.traceMdl = QtGui.QStandardItemModel()
        self.traceList.setModel(self.traceMdl)

        labels = ["Trace","axis"]
        self.traceMdl.setHorizontalHeaderLabels(labels)
        self.traceMdl.setColumnCount(len(labels))

        self.plot = pg.PlotWidget(self)
        l.addWidget(self.plot)
        l.addWidget(self.traceList)
        
        self.setWidget(w)

    def togglehide(self):
        self.setVisible(self.isHidden())

    def addTraces(self):
        tree = self.rootapp.plugins["datatree"].widget.tree
        data = self.rootapp.plugins["datatree"].data
        mdl = data.mdl
        target = self.traceMdl.invisibleRootItem()

        traceItems = []
        selectedIdxs =  tree.selectedIndexes()
        for idx in selectedIdxs:
            item = mdl.itemFromIndex(idx)
            valueitem = item.data(DATA_VALUEITEM)
            if valueitem and valueitem not in traceItems:
                traceItems.append(valueitem)
        if not traceItems: return
        addItems = []
        remItems = []
        existingNames = dict( ( (target.child(idx).text(),idx) for idx in range(target.rowCount()) ) )
        for x in traceItems:
            name = ".".join(data.getFullName(x))
            if name in existingNames:   remItems.append((name, x, existingNames[name]))
            else:                       addItems.append((name, x))

        for ri in sorted(remItems, key=lambda x:x[2], reverse=True):
            name = ri[0]
            self.rootplugin.buffers[name].usecount-=1
            if self.rootplugin.buffers[name].usecount<=0:
                self.rootplugin.buffers.pop(name)
            target.removeRow(ri[2])
            self.traces.pop(name)
        for ai in addItems:
            name = ai[0]
            qtItem = QtGui.QStandardItem(name)
            qtItem.setData(ai[1],DATA_VALUEITEM)
            target.appendRow(qtItem)
            buffer = self.rootplugin.buffers.get(name)
            if not buffer: self.rootplugin.buffers[name] = Buffer(ai[1])
            self.rootplugin.buffers[name].usecount+=1
            self.traces[name] = self.plot.plot(self.rootplugin.buffers[name]._buf)
        
            self.setHidden(False)

class Buffer():
    def __init__(self, datasrc):
        self._buf = deque(1000*[0],1000)
        self.datasrc = datasrc
        self.usecount = 0
    def update(self):
        self._buf.append(self.datasrc.value)