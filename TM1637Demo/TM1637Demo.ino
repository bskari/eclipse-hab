//  TM1637TinyDisplay DEMO Sketch
//  This is a demo sketch for the Arduino TM1637TinyDisplay LED Display library
//
//  Author: Jason A. Cox - @jasonacox
//  Date: 2 July 2020
//

// Includes
#include <Arduino.h>
#include <TM1637TinyDisplay.h>
#include "display.hpp"
#include "sensors.hpp"

const int shortDelay_ms = 1000;
const int longDelay_ms = 2000;

void setup() {
  setupDisplay();
}

// TODO(bskari): Delete this
static const int CLK = 22;
static const int DIO = 21;
// Initialize TM1637TinyDisplay - 4 Digit Display
static TM1637TinyDisplay display(CLK, DIO);

void loop() {
  display.setBrightness(8);
  
  // Demo for balloon
  display.showString("ALTI");
  delay(shortDelay_ms);
  display.showNumber(1, false, 4, 0);    // Number, leading zero=false, length=1, position=0 (left)
  delay(shortDelay_ms);
  display.showNumber(4853, false, 4, 0);    // Number, leading zero=false, length=4, position=0 (left)
  delay(longDelay_ms);
  
  display.showString("ASCE");
  delay(shortDelay_ms);
  display.clear();
  display.showString("5_27");
  delay(longDelay_ms);
  display.clear();
  
  display.showString("TEMP");
  delay(shortDelay_ms);
  display.clear();
  display.showString("\xB0", 1, 3);        // Degree Mark, length=1, position=3 (right)
  display.showNumber(-39, false, 3, 0);    // Number, length=3, position=0 (left)
  delay(longDelay_ms);
  display.clear();
  
  display.showString("LATI");
  delay(shortDelay_ms);
  display.clear();
  display.showNumber(39, false, 2, 2);    // Number, colon, leading zero=false, length=2, position=2
  delay(longDelay_ms);
  display.showNumber(9966, false, 4, 0);    // Number, leading zero=false, length=4, position=0 (left)
  delay(longDelay_ms);
  display.clear();
  
  display.showString("LONG");
  delay(shortDelay_ms);

  display.clear();
  display.showNumber(-105, false, 4, 0);    // Number, colon, leading zero=false, length=4, position=0 (left)
  delay(longDelay_ms);
  display.showNumber(2311, false, 4, 0);    // Number, leading zero=false, length=4, position=0 (left)
  delay(longDelay_ms);
  display.clear();
}
