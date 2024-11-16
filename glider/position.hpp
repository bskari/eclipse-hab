#include <Adafruit_LSM303DLH_Mag.h>
#include <Adafruit_LSM303_Accel.h>
#include <Adafruit_Sensor.h>
#include <TinyGPSPlus.h>
#include <Wire.h>

struct Position {
  float latitude_d;
  float longitude_d;
  float altitude_m;
  bool valid;
  float pitch_d;
  float roll_d;
  float yaw_d;
};

class PositionEstimator {
public:
  PositionEstimator();
  ~PositionEstimator() = default;
  void update();
  Position get();

private:
  // Need to assign a unique ID ot each sensor
  Adafruit_LSM303DLH_Mag_Unified mag;
  Adafruit_LSM303_Accel_Unified accel;

  TinyGPSPlus gps;

  float pitch_d;
  float roll_d;
  float yaw_d;

  static void resetGps();
};
