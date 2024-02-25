#ifndef DISPLAY_HPP
#define DISPLAY_HPP

enum class DisplayState_t {
  Altitude = 0,
  VerticalSpeed,
  HorizontalSpeed,
  Temperature,
  Latitude,
  Longitude,
};
const int DISPLAY_STATE_COUNT = 6;
static_assert(DISPLAY_STATE_COUNT == static_cast<int>(DisplayState_t::Longitude) + 1);

enum class ScreenState_t {
  Info = 0,
  Display1,
  Display2,
};


void setupDisplay();

/**
 * Update the display if needed, and switch to the next state, if needed.
 */
void tickDisplay();

#endif
