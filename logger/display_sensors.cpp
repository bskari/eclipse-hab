#include <stdlib.h>
#include <math.h>

#include "SparkFun_u-blox_GNSS_Arduino_Library.h"
#include "Zanshin_BME680.h"

#include "display_sensors.hpp"

// Right now, these just return test data. You'll need to replace these with
// real functions that return data from the sensors or GPS.

extern SFE_UBLOX_GNSS gnss_sensor;
extern BME680_Class env_sensor;

static const float TEN_TO_THE_SEVENTH = 10 * 10 * 10 * 10 * 10 * 10 * 10;
static const float DIVIDER = 1.0 / TEN_TO_THE_SEVENTH;

float getLatitude_d() {
  return ((float)gnss_sensor.getLatitude()) * DIVIDER;
}

float getLongitude_d() {
  return ((float)gnss_sensor.getLongitude()) * DIVIDER;
}

float getAltitude_m() {
  static decltype(millis()) previousReadingTime_ms = 0;
  static float previousAltitude_m = gnss_sensor.getAltitude() / 1000;

  // Reread altitude 3 seconds
  if (millis() - previousReadingTime_ms > 3000) {
    previousAltitude_m = gnss_sensor.getAltitude() / 1000;
    const float diff_ms = millis() - previousReadingTime_ms;
    previousReadingTime_ms = millis();
  }
  const float diff_ms = millis() - previousReadingTime_ms;
  const float diff_s = diff_ms * 1000;
  return diff_s * getVerticalSpeed_mps() + previousAltitude_m;
}

float getVerticalSpeed_mps() {
  // We don't want to use getAltitude_m here, because it returns estimates. Read directly from the sensor.
  static float previousAltitude_m = gnss_sensor.getAltitude() / 1000;
  static decltype(millis()) previousReadingTime_ms = 0;
  static float speed_mps = 1.0;

  // Recalculate every 10 seconds
  if (millis() - previousReadingTime_ms > 10000) {
    const float diff_ms = millis() - previousReadingTime_ms;
    if (diff_ms == 0) {
      return 1.0;
    }
    previousReadingTime_ms = millis();

    const float currentAltitude_m = gnss_sensor.getAltitude() / 1000;
    const float diff_s = diff_ms * 1000;
    speed_mps = (currentAltitude_m - previousAltitude_m) / diff_s;
    previousAltitude_m = currentAltitude_m;
  }
  return speed_mps;
}

float getHorizontalSpeed_mps() {
  return gnss_sensor.getGroundSpeed() / 1000;
}

float getTemperature_c() {
  int32_t temp_centidegreesC, humidity, pressure, gas;  // BME readings
  env_sensor.getSensorData(temp_centidegreesC, humidity, pressure, gas);  // Get readings
  return temp_centidegreesC / 100;
}
