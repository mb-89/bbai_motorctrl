import os
import struct
from mmap import mmap

class Pin():
    def __init__(self, nr, reg, header, pin):
        self.nr = nr
        self.reg = reg
        self.bank = (nr//32)+1
        self.gpiobit = nr%32
        self.header = header
        self.pin = pin

HEADERPINS = [
    Pin(74,0x150c,8,12),
    Pin(75,0x1510,8,11),
    Pin(105,0x1588,8,18)
]

OFFSET_GPIO_DATAIN  =  0x138
SIZE_GPIO           =  0x198
SIZE_GPIOBANK       =  0x2000
OFFSET_GPIOBANK0    =  0x48051000

fmt = "<L"
fmtsize =  struct.calcsize(fmt)

class GPIOplugin():
    def __init__(self, rootapp):
        self.rootapp = rootapp
        self.registeredGPIOs = {}
        self.gpioBanks = {}
        self._gpiofds= {}

    def start(self):pass

    def getPinHandler(self, header, pin):
        if header is not None and pin is not None:
            matches = (x for x in HEADERPINS if x.header == header)
            matches = [x for x in matches if x.pin == pin]
            fnd = matches[0] if len(matches) == 1 else None
            if not fnd: return None

            handler = self.registeredGPIOs.get(fnd.nr)
            if handler is None: handler = GPIOhandler(fnd, self)
            self.registeredGPIOs[fnd.nr] = handler
            return handler

    def openGPIOBank(self, nr):
        fd = open("/dev/mem", "r+b" )
        mem = mmap(fd.fileno(), SIZE_GPIO, offset=OFFSET_GPIOBANK0+nr*SIZE_GPIOBANK)
        self._gpiofds[nr] = fd
        self.gpioBanks[nr] = mem

        return self.gpioBanks[nr]

    def __del__(self):
        for k,v in self.gpioBanks.items(): v.close()
        for k,v in self._gpiofds.items():  v.close()

class GPIOhandler():
    def __init__(self, pinInfo, parent):
        self.parent = parent
        self.pinInfo = pinInfo
        self.rootapp = parent.rootapp

        #if the pin is not exposed in the os, do it:
        osOk = os.system(f"cat /sys/class/gpio/gpio{pinInfo.nr}/value > /dev/null 2>&1") == 0
        if not osOk: osOk = os.system(f"echo {pinInfo.nr} > /sys/class/gpio/export > /dev/null 2>&1") == 0

        #open the needed shared mem
        mem = parent.gpioBanks.get(self.pinInfo.bank)
        if not mem: mem = parent.openGPIOBank(self.pinInfo.bank)
        memOk = mem is not None

        self.isValid = osOk and memOk

    def read(self):
        if not self.isValid: return -1
        memval = self.parent.gpioBanks[self.pinInfo.bank][OFFSET_GPIO_DATAIN:OFFSET_GPIO_DATAIN+fmtsize]
        memval = struct.unpack(fmt, memval)[0]
        return bool( memval & (1<<self.pinInfo.gpiobit) )

    def write(self):
        return -1