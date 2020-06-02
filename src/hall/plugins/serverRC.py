class ServerRCPlugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp

    def getActionDict(self):
        return {
            "kill": (self.killserver, f"Ctrl+k"),
            "start": (self.startserver, f"Ctrl+s")
        }
    
    def killserver(self):
        self.rootapp.downstreamvars["sys.ref.kill"].value = 1

    def startserver(self):
        self.rootapp.plugins["datatree"].start()
        #use ssh connection to start app on the bbai

    def start(self):
        pass