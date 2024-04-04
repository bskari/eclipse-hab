#include <stdlib.h>
#include <math.h>

#include "SparkFun_u-blox_GNSS_Arduino_Library.h"

// Right now, these just return test data. You'll need to replace these with
// real functions that return data from the sensors or GPS.

extern SFE_UBLOX_GNSS gnss_sensor;

float randNegOneToOne() {
  return (float)(rand() - RAND_MAX / 2) / RAND_MAX;
}

float getLatitude_d() {
  return gnss_sensor.getLatitude();
}

float getLongitude_d() {
  static int count = 0;
  if (count < 2) {
    ++count;
    return -105.2345;
  }
  return randNegOneToOne() * 170.0f;
}

float getAltitude_m() {
  static int altitude = 50;

  if (altitude > 420 && altitude < 500) {
    altitude = 9990;
  }
  return altitude += 1.5 + randNegOneToOne();
}

float getVerticalSpeed_mps() {
  static int count = 0;
  if (count < 1) {
    ++count;
    return -1.03;
  }
  return randNegOneToOne() * 50.0f;
}

float getHorizontalSpeed_mps() {
  static int count = 0;
  if (count < 1) {
    ++count;
    return 1.03;
  }
  return fabs(randNegOneToOne() * 50.0f);
}

float getTemperature_c() {
  const float temps[] = {0.0f, -1.2f, 1.2f, -70.0f, 70.0f};
  static int count = 0;
  if (count < sizeof(temps) / sizeof(temps[0])) {
    ++count;
    return temps[count];
  }
  return randNegOneToOne() * 70.0f;
}
