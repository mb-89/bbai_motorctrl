cp HW.dts /home/BeagleBoard-DeviceTrees/src/arm/am5729-beagleboneai-hall.dts
(cd /home/BeagleBoard-DeviceTrees && make src/arm/am5729-beagleboneai-hall.dtb)
cp /home/BeagleBoard-DeviceTrees/src/arm/am5729-beagleboneai-hall.dtb /boot/dtbs
#(configure: dtb=am5729-beagleboneai-hall.dtb) @ boot/uEnv.txt