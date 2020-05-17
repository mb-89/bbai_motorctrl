import os
from mmap import mmap
import struct
import itertools
import time

OFFSET_GPIO_DATAIN  =  0x138
SIZE_GPIO           =  0x198
OFFSET_GPIO3        =  0x48057000
OFFSET_GPIO4        =  0x48059000

fmt = "<L"
fmtsize =  struct.calcsize(fmt)

def main():
    registerGPIO(74)    #pin 8.12 = 3_10
    registerGPIO(75)    #pin 8.11 = 3_11
    registerGPIO(105)   #pin 8.18 = 4_9

    gpio3 = Mem(OFFSET_GPIO3, SIZE_GPIO)
    gpio4 = Mem(OFFSET_GPIO4, SIZE_GPIO)

    while(True):
        readHallSensors(gpio3,gpio4)
        time.sleep(1)

def readHallSensors(mem3,mem4):
    data3 = mem3.read(OFFSET_GPIO_DATAIN, fmt, size = fmtsize)[0]
    data4 = mem4.read(OFFSET_GPIO_DATAIN, fmt, size = fmtsize)[0]

    h1 = int((data3 & (1<<10))>0)
    h2 = int((data3 & (1<<11))>0)
    h3 = int((data4 & (1<<9))>0)

    print(h1,h2,h3)


def printGPIODATAIN(mem):
    data = mem.read(OFFSET_GPIO_DATAIN, fmt, size = fmtsize)
    datastr = f"{data[0]:b}"
    datastrSplit = [''.join(x) for x in itertools.zip_longest(*[iter(datastr)]*4, fillvalue=' ')]
    print(datastrSplit)

def registerGPIO(GPIOnr):
    exists = os.system(f"cat /sys/class/gpio/gpio{GPIOnr}/value > /dev/null 2>&1") == 0
    if exists: return
    os.system(f"echo {GPIOnr} > /sys/class/gpio/export > /dev/null 2>&1")

class Mem():
    def __init__(self, offset, size):
        self._fd = open("/dev/mem", "r+b" )
        self._mem = mmap(self._fd.fileno(), size, offset=offset)
    
    def read(self,offset,format, size = None):
        if size is None: size = struct.calcsize(format)
        return struct.unpack(format, self._mem[offset:offset+size])

    def __del__(self):
        self._mem.close()
        self._fd.close()



if __name__ == "__main__":main()