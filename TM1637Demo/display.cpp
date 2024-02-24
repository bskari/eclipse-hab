#include "display.hpp"
#include "sensors.hpp"
#include <Arduino.h>

// Define Digital Pins
static const int CLK = 22;
static const int DIO = 21;

static void renderDisplay();
static void renderSpeed(const float speed);
static void goToNextState();
static int getTenThousandsAltitude_m();
static int getAltitudePart_m();

// Initialize TM1637TinyDisplay - 4 Digit Display
static TM1637TinyDisplay display(CLK, DIO);

static DisplayState_t displayState = DisplayState_t::Altitude;
static PartState_t partState = PartState_t::Info;
static auto next_ms = millis();


void setupDisplay() {
  display.begin();
}

void tickDisplay() {
  // We always want to update altitude display
  if (displayState == DisplayState_t::Altitude && partState != PartState_t::Info) {
    renderDisplay();
    if (millis() > next_ms) {
      goToNextState();
    }
  } else if (millis() > next_ms) {
    renderDisplay();
    goToNextState();
  }
}

static void renderDisplay() {
  display.clear();
  switch (displayState) {
    case DisplayState_t::Altitude:
      switch (partState) {
        case PartState_t::Info:
          display.showString("ALTI");
          break;
        case PartState_t::Display1:
          {
            const int altitudeTenThousands = getTenThousandsAltitude_m();
            if (altitudeTenThousands != 0) {
              // This is janky, but we shouldn't be above 100km or below 0m anyway
              if (altitudeTenThousands < 10) {
                // Number, leading zero=false, length=4, position=0 (0=left)
                display.showNumber(altitudeTenThousands, 4, 3);
              } else {
                display.showNumber(altitudeTenThousands, 4, 2);
              }
            }
          }
          break;
        case PartState_t::Display2:
          {
            const int altitudePart = getAltitudePart_m();
            display.showNumber(altitudePart);
          }
          break;
      }
      break;

    case DisplayState_t::VerticalSpeed:
      switch (partState) {
        case PartState_t::Info:
          display.showString("VERT");
          break;
        case PartState_t::Display1:
          renderSpeed(getVerticalSpeed_mps());
          break;
        case PartState_t::Display2:
          break;
      }
      break;

    case DisplayState_t::HorizontalSpeed:
      switch (partState) {
        case PartState_t::Info:
          display.showString("HORI");
          break;
        case PartState_t::Display1:
          renderSpeed(getHorizontalSpeed_mps());
          break;
        case PartState_t::Display2:
          break;
      }
      break;

    case DisplayState_t::Temperature:
      switch (partState) {
        case PartState_t::Info:
          display.showString("TEMP");
          break;
        case PartState_t::Display1:
          {
            const float temperature = getTemperature_c();
            const int wholeTemperature = temperature;
            // It's not going to be < -99 C or above 999 C, just fudge it
            char buffer[5];
            const int length = snprintf(buffer, 5, "%d", wholeTemperature);
            buffer[4] = '\0';
            display.showString(buffer, false, length, 3 - length);
            display.showString("\xB0", 1, length);
            display.showString(buffer);
            break;
          }
        case PartState_t::Display2:
          break;
      }
      break;

    case DisplayState_t::Latitude:
      switch (partState) {
        case PartState_t::Info:
          display.showString("LATI");
          break;
        case PartState_t::Display1:
          {
            const float latitude = getLatitude_d();
            char buffer[5];
            snprintf(buffer, 5, "%f", latitude);
            int decimalIndex = 0;
            while (buffer[decimalIndex] != '.' && decimalIndex < 4) {
              ++decimalIndex;
            }
            buffer[decimalIndex] = '\0';
            break;
          }
        case PartState_t::Display2:
          break;
      }
      break;

    case DisplayState_t::Longitude:
      break;
  }
}

static void renderSpeed(const float speed) {
  char buffer[5];
  const int whole = speed;
  const int part1 = (speed - whole) * 100;
  const int part = part1 > 0 ? part1 : -part1;
  #pragma GCC diagnostic ignored "-Wformat-truncation"
  snprintf(buffer, 5, "%d_%d", whole, part);
  buffer[4] = '\0';
  display.showString(buffer);
}

static void goToNextState() {
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
