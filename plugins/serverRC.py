import logging
import sys
from PyQt5 import  QtWidgets, QtCore
import paramiko
import os.path as op
import os

class Plugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        if self.rootapp.isServer:
            self.rootapp.log.error("Plugin 'serverRC' is not compatible to server-side and will be skipped.")
            return
        self.sshcon = None
        self.sshlog = logging.getLogger("bbai_motorctrl.server")

    def start(self):pass

    def remoterun(self):
        if self.sshcon: return
        #start ssh connection
        self.sshcon = paramiko.SSHClient()
        self.sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshcon.connect("192.168.0.20", username="root", password="bbai")#yeah i know.

        #create ramdisk
        self.sshExec('mkdir /var/run/motorctrl_ramdisk_py', wait=True)
        self.sshExec('mount -t ramfs ramfs /var/run/motorctrl_ramdisk_py', wait=True)

        #copy stuff to ramdisk
        srcbasepath = op.abspath(op.join(op.dirname(__file__),".."))
        dst = "/var/run/motorctrl_ramdisk_py"
        with self.sshcon.open_sftp() as sftp:
            src1 = op.join(srcbasepath,"plugins")
            dst1 = op.join(dst,"plugins").replace("\\","/")
            sftp.mkdir(dst1)
            self.recursiveput(sftp, src1, dst1)

            src2 = op.join(srcbasepath,"server")
            dst2 = op.join(dst,"server").replace("\\","/")
            sftp.mkdir(dst2)
            self.recursiveput(sftp, src2, dst2)

            sftp.put(op.join(srcbasepath,"__main__.py"), op.join(dst,"__main__.py").replace("\\","/"))

        #start server (we dont wait, but we connect stderr and stdout to our logger)
        stdin, stdout, stderr = self.sshcon.exec_command(f'cd {dst};python3 __main__.py')
        stdout.channel.settimeout(0.01)
        stderr.channel.settimeout(0.01)
        QtCore.QTimer.singleShot(10,lambda: self.remoteread([stdout.channel,stderr.channel]))
        self.rootapp.log.debug("started remote server code")

    def remoteread(self, inputs):
        for read in inputs:
            try:
                str = read.recv(32768).decode("utf-8").split("\n")
            except:
                str = []
            for x in str:
                x = [y for y in x.split("\t") if y]
                if not x:continue
                if x[0] == "INFO":
                    msg = "\t".join(x[1:])
                    self.sshlog.info(msg)
                elif x[0] == "DEBUG":
                    msg = "\t".join(x[1:])
                    self.sshlog.debug(msg)
                elif x[0] == "WARNING":
                    msg = "\t".join(x[1:])
                    self.sshlog.warning(msg)
                elif x[0] == "ERROR":
                    msg = "\t".join(x[1:])
                    self.sshlog.warning(msg)
                elif x[0] == "CRITICAL":
                    msg = "\t".join(x[1:])
                    self.sshlog.critical(msg)
                else:
                    msg = "\t".join(x)
                    self.sshlog.info(msg)

        if not inputs[0].exit_status_ready() and not inputs[1].exit_status_ready():
            QtCore.QTimer.singleShot(10,lambda: self.remoteread(inputs))

    def remotestop(self):
        if not self.sshcon: return
        self.sshExec(chr(3))
        self.sshcon.close()
        self.sshcon = None
        self.rootapp.log.debug("stopped remote server code")

    def stop(self):
        self.remotestop()

    def getActionDict(self):
        return {
            "stop": (self.remotestop, f"Ctrl+k"),
            "start": (self.remoterun, f"Ctrl+s")
        }

    def __del__(self): self.stop()

    def sshExec(self, cmd, wait=False):
        stdin, stdout, stderr = self.sshcon.exec_command(cmd)
        if wait: stdout.channel.recv_exit_status()

    def recursiveput(self, sftp, src, dst):
        for x in os.listdir(src):
            fpsrc = op.join(src, x)
            if op.isfile(fpsrc):
                fpdst = op.join(dst, x).replace("\\","/")
                sftp.put(fpsrc,fpdst)
            elif op.isdir(fpsrc):
                fpdst = op.join(dst, x).replace("\\","/")
                sftp.mkdir(fpdst)
                self.recursiveput(sftp,fpsrc,fpdst)