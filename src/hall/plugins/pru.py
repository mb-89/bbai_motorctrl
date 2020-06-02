import os

class PRUPlugin():
    def __init__(self, rootapp): 
        self.rootapp = rootapp

    def start(self):
        os.system("echo 'am57xx-pru2_0-fw-DF45S024050A2drvr' > /sys/class/remoteproc/remoteproc6/firmware")
        os.system("echo 'start' > /sys/class/remoteproc/remoteproc6/state")

    def stop(self):
        os.system("echo 'stop' > /sys/class/remoteproc/remoteproc6/state")