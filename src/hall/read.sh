#!/bin/bash
#!WRONG! use "show-pins" to see pin usage/cfg <--no, this does not work bc the mappings are wrong
#use "cat /proc/device-tree/chosen/base_dtb" to see if the correct device tree was loaded

#echo 74 > /sys/class/gpio/export #pin 8.12
#echo 75 > /sys/class/gpio/export #pin 8.11
#echo 105 > /sys/class/gpio/export #pin 8.18

while :
do
    echo $(cat /sys/class/gpio/gpio74/value && cat /sys/class/gpio/gpio75/value && cat /sys/class/gpio/gpio105/value)
    sleep 0.25
done
