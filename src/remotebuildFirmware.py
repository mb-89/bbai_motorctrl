import paramiko
import os.path as op
import os

def main():
    TARGET = "/var/run/motorctrl_ramdisk_firmwarebuild"
    #start ssh connection
    sshcon = paramiko.SSHClient()
    sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshcon.connect("192.168.0.20", username="root", password="bbai")#yeah i know.
    #create ramdisk
    stdin, stdout, stderr = sshcon.exec_command(f'mkdir {TARGET}')
    stdin, stdout, stderr = sshcon.exec_command(f'shopt -s globstar')
    stdout.channel.recv_exit_status()
    stdin, stdout, stderr = sshcon.exec_command(f'mount -t ramfs ramfs {TARGET}')
    stdout.channel.recv_exit_status()

    #copy stuff to ramdisk
    stdin, stdout, stderr = sshcon.exec_command(f'mkdir {TARGET}/pru'); stdout.channel.recv_exit_status()
    stdin, stdout, stderr = sshcon.exec_command(f'mkdir {TARGET}/dtbo'); stdout.channel.recv_exit_status()

    with sshcon.open_sftp() as sftp: 
        recursiveput(sftp, op.abspath(op.join(op.dirname(__file__),"pru")), TARGET+"/pru")
        recursiveput(sftp, op.abspath(op.join(op.dirname(__file__),"dtbo")), TARGET+"/dtbo")

    #call the makefiles
    runandwait(sshcon, f"dos2unix {TARGET}/**")

    runandwait(sshcon, f"cd {TARGET}/dtbo; chmod +x ./mk.sh; ./mk.sh")
    runandwait(sshcon, f"cd {TARGET}/pru; chmod +x ./mk.sh; ./mk.sh")

def runandwait(sshcon, cmd):
    stdin, stdout, stderr = sshcon.exec_command(cmd)
    stdout.channel.recv_exit_status()
    tmp = stdout.read().decode('utf-8').strip()
    for x in tmp.split("\n"):
        if x:print(x)
    tmp = stderr.read().decode('utf-8').strip()
    for x in tmp.split("\n"):
        if x:print(x)
def recursiveput(sftp, src, dst):
    for x in os.listdir(src):
        fpsrc = op.join(src, x)
        if op.isfile(fpsrc):

            fpdst = op.join(dst, x).replace("\\","/")
            sftp.put(fpsrc,fpdst)
        elif op.isdir(fpsrc):
            fpdst = op.join(dst, x).replace("\\","/")
            sftp.mkdir(fpdst)
            recursiveput(sftp,fpsrc,fpdst)

if __name__ == "__main__":
    main()