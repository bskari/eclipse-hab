// Demo sketch for the TM1637 display.
// You'll need to install the TM1637TinyDisplay LED display library
// Pin connections:
// TM1637   Arduino
// power    5V or Vin
// ground   ground
// CLK      any pin, just change the CLK definition in display.cpp
// DIO      any pin, just change the DIO definition in display.cpp

// Includes
#include <Arduino.h>
#include "display.hpp"
#include "sensors.hpp"

void setup() {
  // Call setupDisplay with the desired brightness [0..7]
  setupDisplay(3);
  Serial.begin(115200);
}

void loop() {
  // tickDisplay is nonblocking, so you can just put it in the loop anwyhere.
  // If there's nothing to update, it will just return immediately.
  tickDisplay();
}
