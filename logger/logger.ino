#include <Arduino.h>
#include "Wire.h"
#include "AS726X.h"
#include "SparkFun_AS7331.h"
#include "Zanshin_BME680.h"
#include "SparkFun_u-blox_GNSS_Arduino_Library.h"
#include "MicroNMEA.h"
#include "FS.h"
#include "SD.h"
#include "SPI.h"

#include "display.hpp"
#include "display_sensors.hpp"

// Note! You can't upload while the display is plugged in?!

// You'll need to install the TM1637TinyDisplay LED display library
// Pin connections:
// TM1637   Arduino
// power    5V or Vin
// ground   ground
// CLK      any pin, just change the CLK definition in display.cpp
// DIO      any pin, just change the DIO definition in display.cpp

AS726X visnir_sensor;
SfeAS7331ArdI2C uv_sensor;
BME680_Class env_sensor;
SFE_UBLOX_GNSS gnss_sensor;

void setup() {
  Serial.begin(115200);
  
  delay(5000);
  sd_setup();
  Wire.begin();
  uv_sensor.begin();
  uv_sensor.prepareMeasurement(MEAS_MODE_CMD);
  bme_setup();
  gnss_setup();

  pinMode(12, OUTPUT);
  pinMode(13, OUTPUT);
  digitalWrite(12, LOW);
  digitalWrite(13, LOW);

  // This needs to be done after the sensors have been initialized
  // Call setupDisplay with the desired brightness [0..7]
  setupDisplay(3);
}

void loop() {
  {
    const auto end = millis() + 10000;
    while (millis() < end) {
      tickDisplay();
    }
  }
  digitalWrite(12, HIGH);
  digitalWrite(13, LOW);
  visnir_sensor.begin();
  scan_i2c();
  take_visnir_reading();
  take_uv_reading();
  take_env_reading();
  take_gnss_reading();

  {
    const auto end = millis() + 10000;
    while (millis() < end) {
      tickDisplay();
    }
  }
  digitalWrite(12, LOW);
  digitalWrite(13, HIGH);
  visnir_sensor.begin();
  scan_i2c();
  take_visnir_reading();
  take_uv_reading();
  take_env_reading();
  take_gnss_reading();
}

void scan_i2c() {
  byte error, address;
  int nDevices = 0;

  Serial.println("Scanning for I2C devices ...");
  for(address = 0x01; address < 0x7f; address++){
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0){
      Serial.printf("I2C device found at address 0x%02X\n", address);
      nDevices++;
    } else if(error != 2){
      Serial.printf("Error %d at address 0x%02X\n", error, address);
    }
  }
  if (nDevices == 0){
    Serial.println("No I2C devices found");
  }
}

void bme_setup() {
  env_sensor.begin(I2C_STANDARD_MODE);
  delay(5000);
  env_sensor.setOversampling(TemperatureSensor, Oversample16);  // Use enumerated type values
  env_sensor.setOversampling(HumiditySensor, Oversample16);     // Use enumerated type values
  env_sensor.setOversampling(PressureSensor, Oversample16);     // Use enumerated type values
  env_sensor.setIIRFilter(IIR4);  // Use enumerated type values
  env_sensor.setGas(320, 150);  // 320c for 150 milliseconds
}

void gnss_setup() {
  gnss_sensor.begin();

  gnss_sensor.setI2COutput(COM_TYPE_UBX | COM_TYPE_NMEA); //Set the I2C port to output both NMEA and UBX messages
}

void take_visnir_reading() {
  char buffer[256];

  visnir_sensor.takeMeasurements();
  if (visnir_sensor.getVersion() == SENSORTYPE_AS7262)
  {
    //Visible readings
    snprintf(
      buffer,
      sizeof(buffer),
      "V[%0.0f] B[%0.0f] G[%0.0f] Y[%0.0f] O[%0.0f] R[%0.0f]\n",
      visnir_sensor.getCalibratedViolet(),
      visnir_sensor.getCalibratedBlue(),
      visnir_sensor.getCalibratedGreen(),
      visnir_sensor.getCalibratedYellow(),
      visnir_sensor.getCalibratedOrange(),
      visnir_sensor.getCalibratedRed()
    );
    Serial.print(buffer);
    Serial.print("V[");
    appendFile(SD, "/dataout.txt", "Reading: V[");
    Serial.print(visnir_sensor.getCalibratedViolet(), 2);
    String(visnir_sensor.getCalibratedViolet(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] B[");
    appendFile(SD, "/dataout.txt", "] B[");
    Serial.print(visnir_sensor.getCalibratedBlue(), 2);
    String(visnir_sensor.getCalibratedBlue(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] G[");
    appendFile(SD, "/dataout.txt", "] G[");
    Serial.print(visnir_sensor.getCalibratedGreen(), 2);
    String(visnir_sensor.getCalibratedGreen(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] Y[");
    appendFile(SD, "/dataout.txt", "] Y[");
    Serial.print(visnir_sensor.getCalibratedYellow(), 2);
    String(visnir_sensor.getCalibratedYellow(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] O[");
    appendFile(SD, "/dataout.txt", "] O[");
    Serial.print(visnir_sensor.getCalibratedOrange(), 2);
    String(visnir_sensor.getCalibratedOrange(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] R[");
    appendFile(SD, "/dataout.txt", "] R[");
    Serial.print(visnir_sensor.getCalibratedRed(), 2);
    String(visnir_sensor.getCalibratedRed(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("]\n");
    appendFile(SD, "/dataout.txt", "]\n");
  }  
  else if (visnir_sensor.getVersion() == SENSORTYPE_AS7263)
  {
    snprintf(
      buffer,
      sizeof(buffer),
      "R[%0.0f] S[%0.0f] T[%0.0f] U[%0.0f] V[%0.0f] W[%0.0f]\n",
      visnir_sensor.getCalibratedR(),
      visnir_sensor.getCalibratedS(),
      visnir_sensor.getCalibratedT(),
      visnir_sensor.getCalibratedU(),
      visnir_sensor.getCalibratedV(),
      visnir_sensor.getCalibratedW()
    );
    Serial.print(buffer);
    //Near IR readings
    Serial.print("R[");
    appendFile(SD, "/dataout.txt", "Reading: R[");
    Serial.print(visnir_sensor.getCalibratedR(), 2);
    String(visnir_sensor.getCalibratedR(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] S[");
    appendFile(SD, "/dataout.txt", "] S[");
    Serial.print(visnir_sensor.getCalibratedS(), 2);
    String(visnir_sensor.getCalibratedS(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] T[");
    appendFile(SD, "/dataout.txt", "] T[");
    Serial.print(visnir_sensor.getCalibratedT(), 2);
    String(visnir_sensor.getCalibratedT(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] U[");
    appendFile(SD, "/dataout.txt", "] U[");
    Serial.print(visnir_sensor.getCalibratedU(), 2);
    String(visnir_sensor.getCalibratedU(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] V[");
    appendFile(SD, "/dataout.txt", "] V[");
    Serial.print(visnir_sensor.getCalibratedV(), 2);
    String(visnir_sensor.getCalibratedV(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("] W[");
    appendFile(SD, "/dataout.txt", "] W[");
    Serial.print(visnir_sensor.getCalibratedW(), 2);
    String(visnir_sensor.getCalibratedW(), 2).toCharArray(buffer, 16);
    appendFile(SD, "/dataout.txt", buffer);
    Serial.print("]\n");
    appendFile(SD, "/dataout.txt", "]\n");
  }
}

void take_uv_reading() {
  char buffer[256];

  // Send a start measurement command.
  if(kSTkErrOk != uv_sensor.setStartState(true))
    Serial.println("Error starting reading!");
  
  // Wait for a bit longer than the conversion time.
  delay(2+uv_sensor.getConversionTimeMillis());

  // Read UV values.
  if(kSTkErrOk != uv_sensor.readAllUV())
    Serial.println("Error reading UV.");

  snprintf(
    buffer,
    sizeof(buffer),
    "UVA:%0.0f UVB:%0.0f UVC:%0.0f\n",
    uv_sensor.getUVA(),
    uv_sensor.getUVB(),
    uv_sensor.getUVC()
  );
  Serial.print(buffer);

  Serial.print("UVA:");
  appendFile(SD, "/dataout.txt", "UVA:");
  Serial.print(uv_sensor.getUVA());
  String(uv_sensor.getUVA(), 2).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(" UVB:");
  appendFile(SD, "/dataout.txt", " UVB:");
  Serial.print(uv_sensor.getUVB());
  String(uv_sensor.getUVB(), 2).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(" UVC:");
  appendFile(SD, "/dataout.txt", " UVC:");
  Serial.println(uv_sensor.getUVC());
  String(uv_sensor.getUVC(), 2).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  appendFile(SD, "/dataout.txt", "\n");
}

void take_env_reading() {
  static int32_t  temp, humidity, pressure, gas;  // BME readings
  char buffer[256];
  
  env_sensor.getSensorData(temp, humidity, pressure, gas);  // Get readings

  snprintf(
    buffer,
    sizeof(buffer),
    "TempC:%d.%d Humid%%:%d.%d PresshPa:%d.%d\n",
    temp / 100,
    temp % 100,
    humidity / 1000,
    humidity % 1000,
    pressure / 100,
    pressure % 100
  );
  Serial.print(buffer);

  Serial.print("TempC:");
  appendFile(SD, "/dataout.txt", "TempC:");
  Serial.print(temp / 100);
  String(temp / 100).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(".");
  appendFile(SD, "/dataout.txt", ".");
  Serial.print(temp % 100);
  String(temp % 100).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(" Humid%:");
  appendFile(SD, "/dataout.txt", " Humid%:");
  Serial.print(humidity / 1000);
  String(humidity / 1000).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(".");
  appendFile(SD, "/dataout.txt", ".");
  Serial.print(humidity % 1000);
  String(humidity % 1000).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(" PresshPa:");
  appendFile(SD, "/dataout.txt", " Press hPa:");
  Serial.print(pressure / 100);
  String(pressure / 100).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(".");
  appendFile(SD, "/dataout.txt", ".");
  Serial.print(pressure % 100);
  String(pressure % 100).toCharArray(buffer, 16);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print("\n");
  appendFile(SD, "/dataout.txt", "\n");
}

void take_gnss_reading() {
  char buffer[256];

  const long latitude = gnss_sensor.getLatitude();
  const long longitude = gnss_sensor.getLongitude();
  const long altitude = gnss_sensor.getAltitude();
  const byte SIV = gnss_sensor.getSIV();

  snprintf(
    buffer,
    sizeof(buffer),
    "Lat: %ld Long: %ld (degrees * 10^-7) Alt: %ld (mm) SIV: %d\n",
    latitude,
    longitude,
    altitude,
    SIV
  );
  Serial.print(buffer);

  Serial.print(F("Lat: "));
  appendFile(SD, "/dataout.txt", "Lat: ");
  Serial.print(latitude);
  String(latitude).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);

  Serial.print(F(" Long: "));
  appendFile(SD, "/dataout.txt", " Long: ");
  Serial.print(longitude);
  String(longitude).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(F(" (degrees * 10^-7)"));
  appendFile(SD, "/dataout.txt", " (degrees * 10^-7)");

  Serial.print(F(" Alt: "));
  appendFile(SD, "/dataout.txt", " Alt: ");
  Serial.print(altitude);
  String(altitude).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(F(" (mm)"));
  appendFile(SD, "/dataout.txt", " (mm)");

  Serial.print(F(" SIV: "));
  appendFile(SD, "/dataout.txt", " SIV: "); 
  Serial.print(SIV);
  String(SIV).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);

  Serial.println();

  const auto year = gnss_sensor.getYear();
  const auto month = gnss_sensor.getMonth();
  const auto day = gnss_sensor.getDay();
  const auto hour = gnss_sensor.getHour();
  const auto minute = gnss_sensor.getMinute();
  const auto second = gnss_sensor.getSecond();
  snprintf(
    buffer,
    sizeof(buffer),
    "%d-%02d-%02d %02d:%02d:%02d\n",
    year,
    month,
    day,
    hour,
    minute,
    second
  );
  Serial.print(buffer);

  appendFile(SD, "/dataout.txt", "\n"); 
  Serial.print(year);
  String(year).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print("-");
  appendFile(SD, "/dataout.txt", "-"); 
  Serial.print(month);
  String(month).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print("-");
  appendFile(SD, "/dataout.txt", "-"); 
  Serial.print(day);
  String(day).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(" ");
  appendFile(SD, "/dataout.txt", " "); 
  Serial.print(hour);
  String(hour).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(":");
  appendFile(SD, "/dataout.txt", ":"); 
  Serial.print(minute);
  String(minute).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);
  Serial.print(":");
  appendFile(SD, "/dataout.txt", ":"); 
  Serial.print(second);
  String(second).toCharArray(buffer, 32);
  appendFile(SD, "/dataout.txt", buffer);

  snprintf(
    buffer,
    sizeof(buffer),
    "  Time is %svalid  Date is %svalid\n",
    gnss_sensor.getTimeValid() ? "" : "not " ,
    gnss_sensor.getDateValid() ? "" : "not "
  );
  Serial.print(buffer);


  Serial.print("  Time is ");
  appendFile(SD, "/dataout.txt", "  Time is "); 
  if (gnss_sensor.getTimeValid() == false)
  {
    Serial.print("not ");
    appendFile(SD, "/dataout.txt", "not "); 
  }
  Serial.print("valid  Date is ");
  appendFile(SD, "/dataout.txt", "valid  Date is "); 
  if (gnss_sensor.getDateValid() == false)
  {
    Serial.print("not ");
    appendFile(SD, "/dataout.txt", "not "); 
  }
  Serial.print("valid");
  appendFile(SD, "/dataout.txt", "valid"); 

  Serial.println();
  appendFile(SD, "/dataout.txt", "\n");
}

void writeFile(fs::FS &fs, const char * path, const char * message){
    Serial.printf("Writing file: %s\n", path);

    File file = fs.open(path, FILE_WRITE);
    if(!file){
        Serial.println("Failed to open file for writing");
        return;
    }
    if(file.print(message)){
        Serial.println("File written");
    } else {
        Serial.println("Write failed");
    }
    file.close();
}

void appendFile(fs::FS &fs, const char * path, const char * message){
    File file = fs.open(path, FILE_APPEND);
    if(!file){
        Serial.println("Failed to open file for appending");
        return;
    }
    if(file.print(message)){
    } else {
        Serial.println("Append failed\n");
    }
    file.close();
}

void sd_setup(){
    if(!SD.begin()){
        Serial.println("Card Mount Failed");
        // blink_led();
    }
    uint8_t cardType = SD.cardType();

    if(cardType == CARD_NONE){
        Serial.println("No SD card attached");
        return;
    }

    Serial.print("SD Card Type: ");
    if(cardType == CARD_MMC){
        Serial.println("MMC");
    } else if(cardType == CARD_SD){
        Serial.println("SDSC");
    } else if(cardType == CARD_SDHC){
        Serial.println("SDHC");
    } else {
        Serial.println("UNKNOWN");
    }

    uint64_t cardSize = SD.cardSize() / (1024 * 1024);
    Serial.printf("SD Card Size: %lluMB\n", cardSize);

    writeFile(SD, "/dataout.txt", "Starting Data Collection\n");
    Serial.printf("Total space: %lluMB\n", SD.totalBytes() / (1024 * 1024));
    Serial.printf("Used space: %lluMB\n", SD.usedBytes() / (1024 * 1024));

  return;
}


void blink_led(){
  pinMode(2, OUTPUT);

  while(true) {
    digitalWrite(2, HIGH);
    delay(1000);
    digitalWrite(2, LOW);
    delay(1000);
  }

  return;
}
