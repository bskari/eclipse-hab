#include <Adafruit_LSM303DLH_Mag.h>
#include <Adafruit_LSM303_Accel.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

/* Assign a unique ID to this sensor at the same time */
Adafruit_LSM303DLH_Mag_Unified mag = Adafruit_LSM303DLH_Mag_Unified(12345);

Adafruit_LSM303_Accel_Unified accel = Adafruit_LSM303_Accel_Unified(54321);

static const int gpsRxPin = 17;
static const int gpsTxPin = 16;

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

void setup(void) {
  Serial.begin(115200);
  Serial.println("Glider test");

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
  Serial.print("Range set to: ");
  lsm303_accel_range_t new_range = accel.getRange();
  switch (new_range) {
  case LSM303_RANGE_2G:
    Serial.println("+- 2G");
    break;
  case LSM303_RANGE_4G:
    Serial.println("+- 4G");
    break;
  case LSM303_RANGE_8G:
    Serial.println("+- 8G");
    break;
  case LSM303_RANGE_16G:
    Serial.println("+- 16G");
    break;
  }
   
  accel.setMode(LSM303_MODE_NORMAL);
  Serial.print("Mode set to: ");
  lsm303_accel_mode_t new_mode = accel.getMode();
  switch (new_mode) {
  case LSM303_MODE_NORMAL:
    Serial.println("Normal");
    break;
  case LSM303_MODE_LOW_POWER:
    Serial.println("Low Power");
    break;
  case LSM303_MODE_HIGH_RESOLUTION:
    Serial.println("High Resolution");
    break;
  }

  displayMagSensorDetails();
  displayAccelSensorDetails();

  Serial2.begin(9600);
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
}

void resetGps() {
  // Controlled software reset
  const byte reset[] = {0xb5, 0x62, 0x06, 0x04, 0x04, 0x00, 0x00, 0x00, 0x02, 0x00, 0x0f, 0x66};
  static_assert(sizeof(reset) == 12);
  Serial2.write(reset, sizeof(reset));
}

char blockingReadFromGps() {
  while (Serial2.available() == 0) {
    // Wait
  }
  return Serial2.read();
}

void loop(void) {
  sensors_event_t event;
  mag.getEvent(&event);

  Serial.print("X: ");
  Serial.print(event.magnetic.x);
  Serial.print("  ");
  Serial.print("Y: ");
  Serial.print(event.magnetic.y);
  Serial.print("  ");
  Serial.print("Z: ");
  Serial.print(event.magnetic.z);
  Serial.print("  ");
  Serial.println("uT");

  accel.getEvent(&event);

  Serial.print("X: ");
  Serial.print(event.acceleration.x);
  Serial.print("  ");
  Serial.print("Y: ");
  Serial.print(event.acceleration.y);
  Serial.print("  ");
  Serial.print("Z: ");
  Serial.print(event.acceleration.z);
  Serial.print("  ");
  Serial.println("m/s^2");

  static char buffer[105];
  static int index = 0;
  while (Serial2.available() > 0) {
    char data = Serial2.read();
    buffer[index] = data;
    ++index;
    if (index >= 100) {
      index = 0;
      Serial.println("Too many");
      Serial.println(buffer);
      buffer[100] = '\0';
    }
    if (data == '*') {
      // Read 4 more, 2 checksum bytes + \r + \n
      for (int i = 0; i < 4; ++i) {
        data = blockingReadFromGps();
        buffer[index] = data;
        if (data != '\r' && data != '\n') {
          ++index;
        }
      }
      buffer[index] = '\0';
      Serial.println(buffer);
      index = 0;
    }
  }

  // Huh, looks like this isn't necessary anymore? Whatever I changed with the read into a buffer
  // above seems to have fixed it. I'll leave this though, just in case.
  if (strncmp(buffer, "$GPTXT", 6) == 0) {
    resetGps();
    index = 0;
    buffer[0] = '\0';
    for (int i = 0; i < 10; ++i) {
      Serial.println("******* Resetting ********");
    }
  }

  delay(500);
}
