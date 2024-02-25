#include "display.hpp"
#include "sensors.hpp"
#ifdef ARDUINO
#include <Arduino.h>
#include <TM1637TinyDisplay.h>
#endif

// Define Digital Pins
static const int CLK = 22;
static const int DIO = 21;

static const int SHORT_DELAY_MS = 1000;
static const int LONG_DELAY_MS = 2000;

static void renderDisplay();
static void renderSpeed_mps(const float speed);
// TODO(bskari): coordinate might need to be a double? I think float can do 7.225 decimal digits, so
// e.g. -105.2314 is going to be close
static void renderCoordinate1(const decltype(getLatitude_d()) coordinate);
static void renderCoordinate2(const decltype(getLatitude_d()) coordinate);
static void goToNextState();
static int getTenThousandsAltitude_m();
static int getAltitudePart_m();

// Initialize TM1637TinyDisplay - 4 Digit Display
#ifdef ARDUINO
static TM1637TinyDisplay display(CLK, DIO);
#else
#include <sys/time.h>
#include <stdio.h>
#include <assert.h>
#include <unistd.h>
#include <curses.h>
int millis() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  return (tv.tv_sec % (24 * 60 * 60)) * 1000 + tv.tv_usec / 1000;
}
struct Display {
  static const int x = 1;
  static const int y = 1;
  void begin() {}
  void clear() {
    wmove(stdscr, y + 1, x);
    wprintw(stdscr, "      ");
    wrefresh(stdscr);
  }
  // String, length=4, position=0 (0=left), dots=0
  void showString(const char* str, const int length = 4, const int position = 0) {
    wmove(stdscr, y, x);
    wprintw(stdscr, "%d ", millis());
    wmove(stdscr, y + 1, x + position);
    wprintw(stdscr, "%.*s", length, str);
    wmove(stdscr, y + 2, x);
    wrefresh(stdscr);
  }
  // Number, leading zero=false, length=4, position=0 (0=left)
  void showNumber(const int num, const bool leadingZero = false, const int length = 4, const int position = 0) {
    wmove(stdscr, y, x);
    wprintw(stdscr, "%d ", millis());
    if (length != 4) {
      wprintw(stdscr, "Unexpected showNumber length? %d", length);
    }
    wmove(stdscr, y + 1, x + position);

    if (leadingZero) {
      wprintw(stdscr, "%0*d", length - position, num);
    } else {
      wprintw(stdscr, "% *d", length - position, num);
    }
    wmove(stdscr, y + 2, x);
    wrefresh(stdscr);
  }
} display;
#endif

static DisplayState_t displayState = DisplayState_t::Altitude;
static ScreenState_t screenState = ScreenState_t::Info;
static auto next_ms = millis();


void setupDisplay() {
  display.begin();
}

void tickDisplay() {
  // We always want to update altitude display
  if (displayState == DisplayState_t::Altitude && screenState != ScreenState_t::Info) {
    if (millis() > next_ms) {
      goToNextState();
    }
    renderDisplay();
  } else if (millis() > next_ms) {
    goToNextState();
    renderDisplay();
  }
}

static void renderDisplay() {
  static decltype(getLatitude_d()) latitude;
  static decltype(getLongitude_d()) longitude;

  display.clear();
  switch (displayState) {
    case DisplayState_t::Altitude:
      switch (screenState) {
        case ScreenState_t::Info:
          display.showString("ALTI");
          break;
        case ScreenState_t::Display1:
          {
            const int altitudeTenThousands = getTenThousandsAltitude_m();
            if (altitudeTenThousands == 0) {
              screenState = ScreenState_t::Display2;
            } else {
              // This is janky, but we shouldn't be above 100km or below 0m anyway
              if (altitudeTenThousands < 10) {
                // Number, leading zero=false, length=4, position=0 (0=left)
                display.showNumber(altitudeTenThousands, true, 4, 3);
              } else {
                display.showNumber(altitudeTenThousands, true, 4, 2);
              }
            }
            #ifndef ARDUINO
            usleep(100000);
            #endif
          }
          break;
        case ScreenState_t::Display2:
          {
            const int altitudeTenThousands = getTenThousandsAltitude_m();
            const bool leadingZeroes = altitudeTenThousands > 0;
            const int altitudePart = getAltitudePart_m();
            display.showNumber(altitudePart, leadingZeroes, 4, 0);
            #ifndef ARDUINO
            usleep(100000);
            #endif
          }
          break;
      }
      break;

    case DisplayState_t::VerticalSpeed:
      switch (screenState) {
        case ScreenState_t::Info:
          display.showString("VERT");
          break;
        case ScreenState_t::Display1:
          renderSpeed_mps(getVerticalSpeed_mps());
          break;
        case ScreenState_t::Display2:
          break;
      }
      break;

    case DisplayState_t::HorizontalSpeed:
      switch (screenState) {
        case ScreenState_t::Info:
          display.showString("HORI");
          break;
        case ScreenState_t::Display1:
          renderSpeed_mps(getHorizontalSpeed_mps());
          break;
        case ScreenState_t::Display2:
          break;
      }
      break;

    case DisplayState_t::Temperature:
      switch (screenState) {
        case ScreenState_t::Info:
          display.showString("TEMP");
          break;
        case ScreenState_t::Display1:
          {
            const float temperature = getTemperature_c();
            const int wholeTemperature = temperature;
            // It's not going to be < -99 C or above 999 C, just fudge it
            char buffer[5];
            // \xB0 is degrees symbol
            snprintf(buffer, 5, "% 3d\xB0", wholeTemperature);
            buffer[4] = '\0';
            display.showString(buffer);
            break;
          }
        case ScreenState_t::Display2:
          break;
      }
      break;

    case DisplayState_t::Latitude:
      switch (screenState) {
        case ScreenState_t::Info:
          // Save the latitude here so that if we roll over during display from e.g. 39.9999 to
          // 40.0001, we don't display 39 then 0001
          latitude = getLatitude_d();
          display.showString("LATI");
          break;
        case ScreenState_t::Display1:
          renderCoordinate1(latitude);
          break;
        case ScreenState_t::Display2:
          renderCoordinate2(latitude);
          break;
      }
      break;

    case DisplayState_t::Longitude:
      switch (screenState) {
        case ScreenState_t::Info:
          // Save the longitude here so that if we roll over during display from e.g. 39.9999 to
          // 40.0001, we don't display 39 then 0001
          longitude = getLongitude_d();
          display.showString("LONG");
          break;
        case ScreenState_t::Display1:
          renderCoordinate1(longitude);
          break;
        case ScreenState_t::Display2:
          renderCoordinate2(longitude);
          break;
      }
      break;
  }
}

static void renderSpeed_mps(const float speed_mps) {
  char buffer[5];
  const int whole = speed_mps;
  const int part1 = (speed_mps - whole) * 100;
  const int part = part1 > 0 ? part1 : -part1;
  #pragma GCC diagnostic ignored "-Wformat-truncation"
  snprintf(buffer, 5, "%d_%02d", whole, part);
  buffer[4] = '\0';
  display.showString(buffer);
}

static void renderCoordinate1(const decltype(getLatitude_d()) coordinate) {
  char buffer[5];
  snprintf(buffer, 5, "%f", coordinate);
  int decimalIndex = 0;
  while (buffer[decimalIndex] != '.' && decimalIndex < 4) {
    ++decimalIndex;
  }
  buffer[decimalIndex] = '\0';
  const int length = decimalIndex;
  display.showString(buffer, length, 4 - length);
}

static void renderCoordinate2(const decltype(getLatitude_d()) coordinate) {
  char buffer[10];
  snprintf(buffer, 10, "%f", coordinate);
  int decimalIndex = 0;
  while (buffer[decimalIndex] != '.' && decimalIndex < 4) {
    ++decimalIndex;
  }
  buffer[decimalIndex + 1 + 4] = '\0';
  display.showString(&buffer[decimalIndex + 1], 4);
}

/**
 * Goes to the next state. Order is:
 * VerticalSpeed
 * HorizontalSpeed
 * Temperature
 * Latitude
 * Longitude
 * Altitude
 */
static void goToNextState() {
  if (screenState == ScreenState_t::Info) {
    screenState = ScreenState_t::Display1;
    next_ms = millis() + LONG_DELAY_MS;
  } else if (screenState == ScreenState_t::Display1) {
    if (displayState == DisplayState_t::VerticalSpeed) {
      displayState = DisplayState_t::HorizontalSpeed;
      screenState = ScreenState_t::Info;
      next_ms = millis() + SHORT_DELAY_MS;
    } else if (displayState == DisplayState_t::HorizontalSpeed) {
      displayState = DisplayState_t::Temperature;
      screenState = ScreenState_t::Info;
      next_ms = millis() + SHORT_DELAY_MS;
    } else if (displayState == DisplayState_t::Temperature) {
      displayState = DisplayState_t::Latitude;
      screenState = ScreenState_t::Info;
      next_ms = millis() + SHORT_DELAY_MS;
    } else {
      screenState = ScreenState_t::Display2;
      next_ms = millis() + LONG_DELAY_MS;
    }
  } else if (screenState == ScreenState_t::Display2) {
    if (displayState == DisplayState_t::Latitude) {
      displayState = DisplayState_t::Longitude;
    } else if (displayState == DisplayState_t::Longitude) {
      displayState = DisplayState_t::Altitude;
    } else if (displayState == DisplayState_t::Altitude) {
      displayState = DisplayState_t::VerticalSpeed;
    } else {
      // This shouldn't happen
      assert(false && "Bad Display2 state?");
    }
    screenState = ScreenState_t::Info;
    next_ms = millis() + SHORT_DELAY_MS;
  }
}

static int getTenThousandsAltitude_m() {
  const float altitudeF = getAltitude_m();
  // This shouldn't be necessary because altitude won't get above 10**8, but just to be safe...
  const int altitude = int(altitudeF) % 100000000;
  const int altitudeTenThousands = (int(altitude) - int(altitude / 10000)) / 10000;
  return altitudeTenThousands;
}

static int getAltitudePart_m() {
  const float altitudeF = getAltitude_m();
  const int altitude = int(altitudeF);
  return altitude % 10000;
}
