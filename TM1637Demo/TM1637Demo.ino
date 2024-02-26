//  TM1637TinyDisplay DEMO Sketch
//  This is a demo sketch for the Arduino TM1637TinyDisplay LED Display library
//
//  Author: Jason A. Cox - @jasonacox
//  Date: 2 July 2020
//

// Includes
#include <Arduino.h>
#include "display.hpp"
#include "sensors.hpp"

void setup() {
  setupDisplay(3);
  Serial.begin(115200);
}

void loop() {
  tickDisplay();
}
