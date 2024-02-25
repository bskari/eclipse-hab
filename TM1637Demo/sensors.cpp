#ifdef ARDUINO
// TODO
#else
#include <stdlib.h>
#include <math.h>
float randNegOneToOne() {
  return (float)(rand() - RAND_MAX / 2) / RAND_MAX;
}

float getLatitude_d() {
  static int count = 0;
  if (count < 2) {
    ++count;
    return 39.99995;
  }
  return randNegOneToOne() * 80.0f;
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

  if (altitude > 120 && altitude < 200) {
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
  static int count = 0;
  if (count < 1) {
    ++count;
    return 0.0f;
  }
  return randNegOneToOne() * 70.0f;
}
#endif
