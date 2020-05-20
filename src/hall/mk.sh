cp HW.dts /home/devicetrees/src/arm/BBAI_HW.dts
cp HW.defines.dtsi /home/devicetrees/src/arm/HW.defines.dtsi
cp HW.ocp.dtsi /home/devicetrees/src/arm/HW.ocp.dtsi
cp HW.misc.dtsi /home/devicetrees/src/arm/HW.misc.dtsi
cp HW.pinmuxer.dtsi /home/devicetrees/src/arm/HW.pinmuxer.dtsi

(cd /home/devicetrees && make src/arm/BBAI_HW.dtb)
cp /home/devicetrees/src/arm/BBAI_HW.dtb /boot/dtbs
#(configure: dtb=am5729-beagleboneai-hall.dtb) @ boot/uEnv.txt