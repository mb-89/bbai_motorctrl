import paramiko
import os.path as op
import os

class ServerRCPlugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        self.sshcon = None

    def getActionDict(self):
        return {
            "kill": (self.killserver, f"Ctrl+k"),
            "reboot": (self.rebootserver, f"Ctrl+Shift+k"),
            "start": (self.startserver, f"Ctrl+s")
        }
    
    def rebootserver(self):
        if not self.sshcon: return
        self.rootapp.downstreamvars["sys.ref.kill"].value = 1
        stdin, stdout, stderr = self.sshcon.exec_command('reboot')
        self.sshcon.close()
        self.sshcon = None

    def killserver(self):
        if not self.sshcon: return
        #stop server
        self.rootapp.downstreamvars["sys.ref.kill"].value = 1
        
        ##unmount ramdisk, delete folder
        #stdin, stdout, stderr = self.sshcon.exec_command('umount /var/run/motorctrl_ramdisk')
        #stdout.channel.recv_exit_status()
        #stdin, stdout, stderr = self.sshcon.exec_command('rm -rf /var/run/motorctrl_ramdisk')
        #stdout.channel.recv_exit_status()

        #close ssh connection
        self.sshcon.close()
        self.sshcon = None

    def startserver(self):
        if self.sshcon: return
        #start ssh connection
        self.sshcon = paramiko.SSHClient()
        self.sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshcon.connect("192.168.0.20", username="root", password="bbai")#yeah i know.
        #create ramdisk
        stdin, stdout, stderr = self.sshcon.exec_command('mkdir /var/run/motorctrl_ramdisk_py')
        stdout.channel.recv_exit_status()
        stdin, stdout, stderr = self.sshcon.exec_command('mount -t ramfs ramfs /var/run/motorctrl_ramdisk_py')
        stdout.channel.recv_exit_status()

        #copy stuff to ramdisk
        src = op.abspath(op.join(op.dirname(__file__),".."))
        dst = "/var/run/motorctrl_ramdisk_py"
        with self.sshcon.open_sftp() as sftp: self.recursiveput(sftp, src,dst)

        #build remote code

        #reset local vars
        self.rootapp.plugins["data"].start()

        #start server
        stdin, stdout, stderr = self.sshcon.exec_command('python3 /var/run/motorctrl_ramdisk_py')
        #we dont wait for this one.

    def __del__(self):
        self.killserver()

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

    def start(self):
        pass