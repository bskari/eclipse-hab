#include <math.h>

#include "position.hpp"

// Need to assign a unique ID to each sensor
PositionEstimator::PositionEstimator()
    : mag(12345),
    accel(54321),
    gps(),
    pitch_d(),
    roll_d(),
    yaw_d()
{
  // Magnetometer
  mag.enableAutoRange(true);
  if (!mag.begin()) {
    Serial.println("Ooops, no LSM303 magnetometer detected... Check your wiring!");
    while (1);
  }

  // Accelerometer
  if (!accel.begin()) {
    Serial.println("Ooops, no LSM303 accelerator detected... Check your wiring!");
    while (1);
  }

  accel.setRange(LSM303_RANGE_4G);
  accel.setMode(LSM303_MODE_NORMAL);

  Serial2.begin(9600);
  // TODO(bskari): Have it output binary instead of NMEA

  // From https://gis.stackexchange.com/questions/198846/enabling-disabling-nmea-sentences-on-u-blox-gps-receiver
  const byte gllOff[] = {0xb5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xf0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x2b, 0xb5, 0x62, 0x06, 0x01, 0x02, 0x00, 0xf0, 0x01, 0xfa, 0x12};
  const byte gsaOff[] = {0xb5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xf0, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x32, 0xb5, 0x62, 0x06, 0x01, 0x02, 0x00, 0xf0, 0x02, 0xfb, 0x13};
  const byte gsvOff[] = {0xb5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xf0, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x03, 0x39, 0xb5, 0x62, 0x06, 0x01, 0x02, 0x00, 0xf0, 0x03, 0xfc, 0x14};
  const byte rmcOff[] = {0xb5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xf0, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x04, 0x40, 0xb5, 0x62, 0x06, 0x01, 0x02, 0x00, 0xf0, 0x04, 0xfd, 0x15};
  const byte vtgOff[] = {0xb5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xf0, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x05, 0x47, 0xb5, 0x62, 0x06, 0x01, 0x02, 0x00, 0xf0, 0x05, 0xfe, 0x16};
  // Changing baud doesn't seem to work
  //const byte baud38400[] = {0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0xD0, 0x08, 0x00, 0x00, 0xF0, 0x87, 0x00, 0x00, 0x07, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x74, 0x24}; 
  Serial2.write(gllOff, sizeof(gllOff));
  Serial2.flush();
  Serial2.write(gsaOff, sizeof(gsaOff));
  Serial2.flush();
  Serial2.write(gsvOff, sizeof(gsvOff));
  Serial2.flush();
  Serial2.write(rmcOff, sizeof(rmcOff));
  Serial2.flush();
  Serial2.write(vtgOff, sizeof(vtgOff));
  Serial2.flush();
  //Serial2.write(baud38400, sizeof(baud38400));
  //Serial2.flush();
  //Serial2.begin(38400);
  Serial.println("Here5");
  delay(100);
}

void PositionEstimator::update() {
  // Read from the sensors
  sensors_event_t event;
  accel.getEvent(&event);
  const float pitch_r = atan2f(-event.acceleration.x, sqrtf(event.acceleration.y * event.acceleration.y + event.acceleration.z * event.acceleration.z));
  const float roll_r = atan2f(event.acceleration.y, event.acceleration.z);

  mag.getEvent(&event);
  const float mxComp = event.magnetic.x * cosf(pitch_r) + event.magnetic.z * sinf(pitch_r);
  const float myComp = event.magnetic.x * sinf(roll_r) * sinf(pitch_r) + event.magnetic.y * cosf(roll_r) - event.magnetic.z * sinf(roll_r) * cosf(pitch_r);
  const float yaw_r = atan2(-myComp, mxComp);

  pitch_d = pitch_r * 180.0 / PI;
  roll_d = roll_r * 180.0 / PI;
  yaw_d = yaw_r * 180.0 / PI;

  while (Serial2.available() > 0) {
    gps.encode(Serial2.read());
  }
}

void PositionEstimator::resetGps() {
  // Controlled software reset
  const byte reset[] = {0xb5, 0x62, 0x06, 0x04, 0x04, 0x00, 0x00, 0x00, 0x02, 0x00, 0x0f, 0x66};
  static_assert(sizeof(reset) == 12);
  Serial2.write(reset, sizeof(reset));
}

Position PositionEstimator::get() {
  Position pos;
  pos.latitude_d = gps.location.lat();
  pos.longitude_d = gps.location.lng();
  pos.altitude_m = gps.altitude.meters();
  pos.valid = gps.location.isValid();
  pos.updated = gps.location.isUpdated();
  const float declinationDenver_d = 7.56f;
  // I mounted this rotated, so we need to adjust
  pos.pitch_d = -roll_d;
  pos.roll_d = -pitch_d;
  // I don't know if we need to add or subtract this declination
  pos.yaw_d = -yaw_d + 90.0f + 360.0f + declinationDenver_d;
  while (pos.yaw_d >= 360.0f) {
    pos.yaw_d -= 360.0f;
  }
  return pos; 
}

/*
void displayMagSensorDetails(void) {
  sensor_t sensor;
  mag.getSensor(&sensor);
  Serial.println("------------------------------------");
  Serial.print("Sensor:       ");
  Serial.println(sensor.name);
  Serial.print("Driver Ver:   ");
  Serial.println(sensor.version);
  Serial.print("Unique ID:    ");
  Serial.println(sensor.sensor_id);
  Serial.print("Max Value:    ");
  Serial.print(sensor.max_value);
  Serial.println(" uT");
  Serial.print("Min Value:    ");
  Serial.print(sensor.min_value);
  Serial.println(" uT");
  Serial.print("Resolution:   ");
  Serial.print(sensor.resolution);
  Serial.println(" uT");
  Serial.println("------------------------------------");
  Serial.println("");
}

void displayAccelSensorDetails(void) {
  sensor_t sensor;
  accel.getSensor(&sensor);
  Serial.println("------------------------------------");
  Serial.print("Sensor:       ");
  Serial.println(sensor.name);
  Serial.print("Driver Ver:   ");
  Serial.println(sensor.version);
  Serial.print("Unique ID:    ");
  Serial.println(sensor.sensor_id);
  Serial.print("Max Value:    ");
  Serial.print(sensor.max_value);
  Serial.println(" m/s^2");
  Serial.print("Min Value:    ");
  Serial.print(sensor.min_value);
  Serial.println(" m/s^2");
  Serial.print("Resolution:   ");
  Serial.print(sensor.resolution);
  Serial.println(" m/s^2");
  Serial.println("------------------------------------");
  Serial.println("");
}
*/
