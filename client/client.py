from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtNetwork

import os.path as op

from plugins.log import Plugin as Plugin_log
from plugins.remotectrl import Plugin as Plugin_remotectrl

class App(QtWidgets.QApplication):
    def __init__(self):
        super().__init__([])
        self.gui = Gui(self)
        self.isServer = False
        self.isClient = True
        self.plugins = {
            "log":Plugin_log(self),
            "remotectrl":Plugin_remotectrl(self)
            }
        self.running = False
        self.aboutToQuit.connect(self.stop)

    def run(self):
        self.gui.start()
        for k,v in self.plugins.items(): v.start()
        self.running = True
        self.exec_()

    def stop(self):
        if not self.running: return
        self.running = False
        for k,v in self.plugins.items(): v.stop()
        self.quit()

    def __del__(self):
        self.stop()

class Gui(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.rootapp = app

        from client import client_ui
        self.ui = client_ui.Ui_ui()
        self.ui.setupUi(self)
        self.rootapp.setApplicationDisplayName("bbai.motorctrl.client")

    def start(self):
        #build plugin menu
        self.ui.PluginsBar = QtWidgets.QMenuBar(self.ui.menuBar)
        self.ui.PluginsMenu= QtWidgets.QMenu("Plugins", self.ui.PluginsBar)
        self.ui.PluginsMenu.plugins = {}
        self.ui.PluginsBar.addMenu(self.ui.PluginsMenu)
        self.ui.menuBar.setCornerWidget(self.ui.PluginsBar)

        #build toolbox
        #self.ui.ToolBox = ToolBox(self.rootapp)
        #self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.ui.ToolBox)

        #register shortcuts
        self.actions = {}
        for k,v in self.rootapp.plugins.items():
            acts = v.getActionDict()
            for actname, act in acts.items():
                self.actions[k+"."+actname] = self.registerAction(k,actname,*act)
        self.show()

    def registerAction(self, pluginname, actname, fn, shortcut = None, ToolbarEntry = None):
        action = QtWidgets.QAction(self)
        action.triggered.connect(fn)
        action.setText(actname)
        self.addAction(action)
        menu = self.ui.PluginsMenu
        plugmenu = menu.plugins.get(pluginname)
        if not plugmenu:
            plugmenu = QtWidgets.QMenu(menu)
            plugmenu.setTitle(pluginname)
            menu.plugins[pluginname] = plugmenu
            menu.addMenu(plugmenu)
        plugmenu.addAction(action)

        if shortcut: action.setShortcut(shortcut)

        return action

class ToolBox(QtWidgets.QDockWidget):
    def __init__(self, app):
        super().__init__()
        self.rootapp = app
        ui = app.gui.ui
        self.widget = QtWidgets.QToolBox(self)
        self.tabs = {}
        self.setWindowTitle('Toolbox')
        self.addTab('Tab1')
        self.addTab('Tab2')

    def addTab(self, name):
        tab = self.widget.addItem(QtWidgets.QWidget(), name)
        self.tabs[name] = tab
