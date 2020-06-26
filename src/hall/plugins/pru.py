import os
from mmap import mmap
import struct

OFFSET_PRU_DATARAM0 = 0x00000000
OFFSET_PRU_ICSS1 = 0x4B200000
OFFSET_PRU_ICSS2 = 0x4B280000

SIZE_PRU_DATARAM0 = 0x2000


class PRUPlugin():
    def __init__(self, rootapp): 
        self.rootapp = rootapp
        self._mem0 = Mem(OFFSET_PRU_ICSS2+OFFSET_PRU_DATARAM0, SIZE_PRU_DATARAM0)

    def start(self):
        os.system("echo 'am57xx-pru2_0-fw-DF45S024050A2drvr' > /sys/class/remoteproc/remoteproc6/firmware")
        os.system("echo 'start' > /sys/class/remoteproc/remoteproc6/state")

    def stop(self):
        self._mem0.close()
        os.system("echo 'stop' > /sys/class/remoteproc/remoteproc6/state")

    def read(self, core, offset, format, size = None):
        if core != 0: return None
        return self._mem0.read(offset, format, size)

    def write(self, values, core, offset, format, size=None):
        if core != 0: return
        self._mem0.write(offset, format, values)

class Mem():
    def __init__(self, offset, size):
        self._fd = open("/dev/mem", "r+b" )
        self._mem = mmap(self._fd.fileno(), size, offset=offset)
    
    def read(self,offset,format, size = None):
        if size is None: size = struct.calcsize(format)
        return struct.unpack(format, self._mem[offset:offset+size])

    def write(self, offset, format, values, size = None):
        if size is None: size = struct.calcsize(format)
        val = struct.pack(format, *values)
        self._mem[offset:offset+size] = val

    def close(self):
        self._mem.close()
        self._fd.close()

    def __del__(self):
        self.close()
