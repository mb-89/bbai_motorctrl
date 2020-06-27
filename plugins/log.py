import logging
import sys
from PyQt5 import  QtWidgets, QtCore

log = None

class Plugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        if      self.rootapp.isServer: self.logger = ServerSideLogger(rootapp)
        elif    self.rootapp.isClient: self.logger = ClientSideLogger(rootapp)
        self.log = self.logger.log
        self.rootapp.log = self.log

    def getActionDict(self): return self.logger.getActionDict()
    def stop(self): return self.logger.stop()
    def start(self): return self.logger.start()

class ServerSideLogger():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        #basic setup
        global log
        log = logging.getLogger("bbai_motorctrl.server")
        self.log = log
        log.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s\t%(message)s')
        log._fmt = formatter

        #on the server side, we send all stuff to stdout and stderr, and the ssh connection
        #will transport it to the client
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(log._fmt)
        log.addHandler(ch)

        #add to file
        #fh = logging.FileHandler("bbai_motorctrl.log",mode="w")
        #fh.setLevel(logging.DEBUG)
        #fh.setFormatter(log._fmt)
        #log.addHandler(fh)

    def getActionDict(self):return {}
    def stop(self): 
        log.debug("stopped server side logging")
    def start(self):
        log.debug("started server side logging")

class ClientSideLogger():
    def __init__(self, rootapp):
        #basic setup
        self.rootapp = rootapp
        global log
        masterlog = logging.getLogger("bbai_motorctrl")
        log = logging.getLogger("bbai_motorctrl.client")
        sshLog = logging.getLogger("bbai_motorctrl.server")

        self.log = log
        masterlog.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(relativeCreated)08d\t%(name)s\t%(levelname)s:\t%(message)s')
        masterlog._fmt = formatter

        #reroute stdin, stderr
        masterlog._STDerrLogger = StreamToLogger(masterlog, logging.ERROR)
        masterlog._origSTDerr = sys.stderr
        masterlog._STDoutLogger = StreamToLogger(masterlog, logging.INFO)
        masterlog._origSTDout = sys.stdout
        #sys.stdout = masterlog._STDoutLogger
        #sys.stderr = masterlog._STDerrLogger

        #add to file
        fh = logging.FileHandler("bbai_motorctrl.log",mode="w")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(masterlog._fmt)
        #masterlog.addHandler(fh)

        #add to statusbar
        widget = self.rootapp.gui.ui.statusBar
        QtHandler = QtLog2StatusBarHandler()
        QtHandler.setFormatter(masterlog._fmt)
        QtHandler.setLevel(logging.DEBUG)
        QtHandler.sig.connect(lambda x: widget.showMessage(x, 0))
        masterlog.addHandler(QtHandler)

        #add to widget
        QtHandler = QtLog2TextEditHandler()
        QtHandler.setFormatter(masterlog._fmt)
        QtHandler.setLevel(logging.DEBUG)
        self.logwidget = LogWidget(self.rootapp)
        QtHandler.sig.connect(self.logwidget.append)
        masterlog.addHandler(QtHandler)

    def getActionDict(self):
        return {"toggle log": (self.logwidget.togglehide, f"Ctrl+L"),}
    def stop(self):
        log.debug("stopped client side logging")
    def start(self): 
        log.debug("started client side logging")

class LogWidget(QtWidgets.QDockWidget):
    def __init__(self, app):
        super().__init__()
        self.rootapp = app
        ui = app.gui.ui
        self.lw = QtWidgets.QPlainTextEdit()
        #self.lw.setReadOnly(True)
        self.lw.setUndoRedoEnabled(False)
        self.hide()
        self.setWidget(self.lw)
        self.rootapp.gui.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self)
        self.resize(600,400)
        self.setWindowTitle('bbai_motorctrl log')
        self.append = self.lw.appendPlainText

    def togglehide(self):
        self.setVisible(self.isHidden())


class StreamToLogger():
    """
    Fake file-like stream object that redirects writes to a logger instance.
    https://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):pass

class QtLog2StatusBarHandler(QtCore.QObject,logging.StreamHandler):
    sig = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()

    def emit(self, logRecord):
        msg = self.format(logRecord)
        self.sig.emit(msg)

class QtLog2TextEditHandler(QtCore.QObject,logging.StreamHandler):
    sig = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()

    def emit(self, logRecord):
        msg = self.format(logRecord)
        self.sig.emit(msg)