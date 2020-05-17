#!/usr/bin/env node  
////////////////////////////////////////  
// blinkLED.js  
//      Blinks the USR LEDs and P9_15 when you connect 3.3V to P9_12.  
// Wiring: P9_15 connects to the plus lead of an LED.  The negative lead of the  
//   LED goes to a 220 Ohm resistor.  The other lead of the resistor goes  
//   to ground.  A jumper goes in the 3.3V header (not 5V!).  Other end goes into  
//         P_12.  Take it in and out to watch light turn on.  
// Setup:  first type the following into the terminal to set up your pins if you haven't...  
//          node -pe "require('bonescript').bone.getPinObject('P9.12').ai.gpio"  
//          node -pe "require('bonescript').bone.getPinObject('P9.15').ai.gpio"  
//  Issues: On first execution, it may through and error due to permissions.  Try running  
//          again.  
////////////////////////////////////////  
const b = require('bonescript');  
const leds = ["USR3"];  
for(var i in leds) {  
    b.pinMode(leds[i], b.OUTPUT);  
}  
b.pinMode("P8_12",b.INPUT);  
var state = b.HIGH;  
for(var i in leds) {  
    b.digitalWrite(leds[i], state);  
}  
setInterval(toggle, 100);  
function toggle() {  
    if (b.digitalRead("P8_12")==b.HIGH)   
        state = b.HIGH;  
    else  
        state = b.LOW;  
    for(var i in leds) {  
        b.digitalWrite(leds[i], state);  
    }  
}  