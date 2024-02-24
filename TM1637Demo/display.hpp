#ifndef DISPLAY_HPP
#define DISPLAY_HPP

#include <TM1637TinyDisplay.h>

enum class DisplayState_t {
  Altitude,
  VerticalSpeed,
  HorizontalSpeed,
  Temperature,
  Latitude,
  Longitude,
};
enum class PartState_t {
  Info,
  Display1,
  Display2,
};


void setupDisplay();

/**
 * Update the display if needed, and switch to the next state, if needed.
 */
void tickDisplay();

#endif
