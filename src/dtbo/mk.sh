#!/bin/bash
dtc -O dtb -o ./BBAI_HW.dtbo -i . ./HW.dts
cp ./BBAI_HW.dtbo /lib/firmware/BBAI_HW.dtbo