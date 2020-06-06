
from PyQt5 import QtCore, QtGui,QtWidgets
from .data import DATA_VALUEITEM

class CalcPlugin():
    def __init__(self, rootapp): 
        self.rootapp = rootapp
        self.mdl = QtGui.QStandardItemModel()
        self.mdl.rootapp = rootapp
        self.mdl.invisibleRootItem().appendRow(CalcObj().getRow())
        self.mdl.itemChanged.connect(lambda x: x.calcItem.validate())
        self.widget = Widget(self, rootapp)

    def start(self):
        self.rootapp.sampleSig.connect(self.sample)
        self.widget.start()

    def stop(self):
        self.widget.stop()

    def sample(self):
        self.mdl.blockSignals(True)
        ri = self.mdl.invisibleRootItem()
        for idx in range(ri.rowCount()):
            item = ri.child(idx)
            if not item.isValid:continue
            item.value = item.fcn(item.srcObj.value)
        self.mdl.blockSignals(False)

    def getActionDict(self):
        return {}

    def getFullName(self, x):
        return [x.calcItem.text()]

class Widget(QtWidgets.QDockWidget):
    def __init__(self, parent, app):
        super().__init__(app.gui)
        self.rootapp = app
        self.rootplugin = parent
        self.setWindowTitle("Calc")
        self.resize(600,400)
        app.gui.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        app.gui.resizeDocks((self,),(1,),QtCore.Qt.Vertical)
        self.setMinimumWidth(150)
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.rootplugin.mdl)

        self.setWidget(self.tree)

        self.updateTimer = QtCore.QTimer()
        self.updateTimer.setInterval(1000)
        self.updateTimer.timeout.connect(self.syncQtVals)

    def start(self):
        self.updateTimer.start()

    def stop(self):
        self.updateTimer.stop()

    def syncQtVals(self):
        ri = self.rootplugin.mdl.invisibleRootItem()
        for idx in range(ri.rowCount()):
            item = ri.child(idx)
            if not item.isValid: item._valueDisplay.setText("")
            else:item._valueDisplay.setText(str(item.value))

    def togglehide(self):
        self.setVisible(self.isHidden())

class CalcObj(QtGui.QStandardItem):
    def __init__(self, name = "<new calc>", src = "<name of src>", formula = "<eg x**2>"):
        super().__init__(name)

        self.value = 0
        self.calcItem = self
        self.setData(self,DATA_VALUEITEM)
        self.isDummy = True

        self.isValid = False
        self.srcObj = None
        self.fcn = None

        self._formulaDisplay = QtGui.QStandardItem(formula)
        self._formulaDisplay.calcItem = self
        self._formulaDisplay.setData(self,DATA_VALUEITEM)
        self._valueDisplay = QtGui.QStandardItem("")
        self._valueDisplay.calcItem = self
        self._valueDisplay.setData(self,DATA_VALUEITEM)
        self._srcDisplay = QtGui.QStandardItem(src)
        self._srcDisplay.calcItem = self
        self._srcDisplay.setData(self,DATA_VALUEITEM)

        self.validate()
    
    def getRow(self):
        return [self, self._srcDisplay, self._formulaDisplay, self._valueDisplay]

    def validate(self):
        newFormula = self._formulaDisplay.text()
        newSrc = self._srcDisplay.text()
        newName = self.text()
        try: mdl = self.model()
        except AttributeError: return

        if any((newFormula.startswith("<"), newSrc.startswith("<"), newName.startswith("<"))):
            self.isValid = False
        else:
            try:
                data = mdl.rootapp.plugins["data"].data
                newLambda = eval("lambda x:"+ newFormula)
                newSrcObj = data.vardict.get(newSrc)
                newVal = newLambda(newSrcObj.value)
                self.srcObj = newSrcObj
                self.fcn = newLambda
                self.isValid = True
            except:
                self.isValid = False
                self.srcObj = None
                self.fcn = None

        if self.isValid and self.isDummy:
            self.isDummy = False
            ri = mdl.invisibleRootItem()
            for idx in range(ri.rowCount()):
                if ri.child(idx).isDummy: break
            else:
                ri.appendRow(CalcObj().getRow())