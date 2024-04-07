// Running on a "DOIT ESP32 DEVKIT V1"
// Install the RemoteXY app on your phone. The demo version should work. Connect to Bluetooth.
// Enter the current time in military time, e.g. "16:32:01" and the cutdown time in the same.
// Use the radio buttons to see the current time, cutdown time, and countdown time.

#include "esp_sleep.h"
#include "esp_wifi.h"
#include "esp_bt_main.h"

/*
   -- balloon-cutdown --

   This source code of graphical user interface
   has been generated automatically by RemoteXY editor.
   To compile this code using RemoteXY library 3.1.11 or later version
   download by link http://remotexy.com/en/library/
   To connect using RemoteXY mobile app by link http://remotexy.com/en/download/
     - for ANDROID 4.11.4 or later version;
     - for iOS 1.9.1 or later version;

   This source code is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2.1 of the License, or (at your option) any later version.
*/

//////////////////////////////////////////////
//        RemoteXY include library          //
//////////////////////////////////////////////

// you can enable debug logging to Serial at 115200
//#define REMOTEXY__DEBUGLOG

// RemoteXY select connection mode and include library
#define REMOTEXY_MODE__ESP32CORE_BLE
#include <BLEDevice.h>

#include <RemoteXY.h>

// RemoteXY connection settings
#define REMOTEXY_BLUETOOTH_NAME "cutdown"

// RemoteXY configurate
#pragma pack(push, 1)
uint8_t RemoteXY_CONF[] =   // 195 bytes
{ 255, 25, 0, 25, 0, 188, 0, 16, 24, 1, 7, 36, 3, 10, 57, 5, 2, 26, 2, 11,
  67, 4, 3, 76, 57, 5, 2, 26, 21, 129, 0, 14, 3, 34, 6, 17, 67, 117, 114, 114,
  101, 110, 116, 32, 116, 105, 109, 101, 0, 7, 36, 3, 25, 57, 5, 2, 26, 2, 11, 3,
  3, 15, 52, 8, 22, 2, 26, 129, 0, 25, 54, 20, 6, 17, 67, 117, 114, 114, 101, 110,
  116, 0, 129, 0, 25, 61, 24, 6, 17, 67, 117, 116, 100, 111, 119, 110, 0, 129, 0, 25,
  68, 31, 6, 17, 67, 111, 117, 110, 116, 100, 111, 119, 110, 0, 1, 0, 22, 87, 7, 7,
  36, 31, 0, 129, 0, 30, 88, 11, 6, 17, 84, 101, 115, 116, 0, 129, 0, 12, 18, 38,
  6, 17, 67, 117, 116, 100, 111, 119, 110, 32, 116, 105, 109, 101, 0, 67, 4, 40, 39, 20,
  5, 2, 26, 4, 129, 0, 11, 32, 42, 6, 17, 66, 117, 114, 110, 32, 100, 117, 114, 97,
  116, 105, 111, 110, 32, 115, 0, 4, 128, 3, 39, 34, 6, 2, 26
};

// this structure defines all the variables and events of your control interface
struct {

  // input variables
  char currentTimeEdit[11];  // string UTF8 end zero
  char cutDownTimeEdit[11];  // string UTF8 end zero
  uint8_t displaySelect; // =0 if select position A, =1 if position B, =2 if position C, ...
  uint8_t testButton; // =1 if button pressed, else =0
  int8_t burnDurationSlider; // =0..100 slider position

  // output variables
  char timeText[21];  // string UTF8 end zero
  char burnDurationText[4];  // string UTF8 end zero

  // other variable
  uint8_t connect_flag;  // =1 if wire connected, else =0

} RemoteXY;
#pragma pack(pop)
/////////////////////////////////////////////
//           END RemoteXY include          //
/////////////////////////////////////////////

#define COUNT_OF(x) (sizeof(x) / sizeof(x[0]))

const int BUTTON_PIN = 0;
const int SWITCH_PIN = 12;
static const int32_t sleepAfterTime_s = 2 * 60;

static bool currentTimeInitialized = false;
static bool cutDownTimeInitialized = false;
static bool armed = false;
static bool lowPower = false;
static int32_t cutDownTime_s = 0;
static int32_t offset_s = 0;
static decltype(millis()) initializedTime_ms = 0;

void setup()
{
  RemoteXY_Init();
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT); // Pressed = LOW
  pinMode(SWITCH_PIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  digitalWrite(SWITCH_PIN, LOW);
  setCpuFrequencyMhz(80);
  Serial.begin(115200);
  RemoteXY.burnDurationSlider = 5;
}

void loop()
{
  if (lowPower) {
    // Sleep
    if (!armed) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(1);
      digitalWrite(LED_BUILTIN, LOW);
    }
    esp_light_sleep_start();
  } else if (currentTimeInitialized && cutDownTimeInitialized && millis() > initializedTime_ms + sleepAfterTime_s * 1000) {
    lowPower = true;
    // Shut off peripherals
    esp_wifi_stop();
    esp_bluedroid_disable();
    esp_bluedroid_deinit();
    esp_bt_controller_disable();
    esp_bt_controller_deinit();
    esp_sleep_enable_timer_wakeup(5 * 1000 * 1000);
  } else {
    RemoteXY_Handler();
    updateDisplay();
    readInputs();
  }
  checkCutdown();
}


void updateDisplay() {
  switch (RemoteXY.displaySelect) {
    case 0: // Current time
      {
        if (!currentTimeInitialized) {
          break;
        }
        const int32_t seconds = millis() / 1000 + offset_s;
        displayTime(seconds);
      }
      break;

    case 1: // Cutdown time
      {
        if (!cutDownTimeInitialized) {
          break;
        }
        displayTime(cutDownTime_s);
      }
      break;

    case 2: // Countdown time
      {
        if (!currentTimeInitialized || !cutDownTimeInitialized) {
          break;
        }
        const int32_t currentSeconds = millis() / 1000 + offset_s;
        const int32_t secondsRemaining = cutDownTime_s - currentSeconds;
        displayTime(secondsRemaining);
      }
      break;
  }
}

void displayTime(const int32_t originalSeconds) {
  const char sign = originalSeconds < 0 ? '-' : ' ';
  const int32_t seconds = originalSeconds > 0 ? originalSeconds : -originalSeconds;
  const int hoursPart = seconds / 3600;
  const int minutesPart = (seconds - hoursPart * 3600) / 60;
  const int secondsPart = (seconds - hoursPart * 3600 - minutesPart * 60);
  snprintf(RemoteXY.timeText, COUNT_OF(RemoteXY.timeText), "%c%02d:%02d:%02d", sign, hoursPart, minutesPart, secondsPart);
}

void readInputs() {
  static char previousCurrentTimeEdit[COUNT_OF(RemoteXY.currentTimeEdit)] = {0};
  static char previousCutDownTimeEdit[COUNT_OF(RemoteXY.cutDownTimeEdit)] = {0};

  int hour, minute, second;
  if (strcmp(RemoteXY.currentTimeEdit, previousCurrentTimeEdit) != 0) {
    // Try to parse
    const int successCount = sscanf(RemoteXY.currentTimeEdit, "%d:%d:%d", &hour, &minute, &second);
    if (successCount == 3) {
      if (hour >= 0 && hour < 24 && minute >= 0 && minute < 60 && second >= 0 && second < 60) {
        offset_s = hour * 3600 + minute * 60 + second - (millis() / 1000);
        currentTimeInitialized = true;
        if (currentTimeInitialized && cutDownTimeInitialized) {
          initializedTime_ms = millis();
        }
      }
    }
  }
  if (strcmp(RemoteXY.cutDownTimeEdit, previousCutDownTimeEdit) != 0) {
    // Try to parse
    const int successCount = sscanf(RemoteXY.cutDownTimeEdit, "%d:%d:%d", &hour, &minute, &second);
    if (successCount == 3) {
      if (hour >= 0 && hour < 24 && minute >= 0 && minute < 60 && second >= 0 && second < 60) {
        cutDownTime_s = hour * 3600 + minute * 60 + second;
        cutDownTimeInitialized = true;
        if (currentTimeInitialized && cutDownTimeInitialized) {
          initializedTime_ms = millis();
        }
      }
    }
  }

  snprintf(RemoteXY.burnDurationText, sizeof(RemoteXY.burnDurationText), "%hhu", getBurnDuration_s());

  strncpy(previousCurrentTimeEdit, RemoteXY.currentTimeEdit, COUNT_OF(previousCurrentTimeEdit));
  strncpy(previousCutDownTimeEdit, RemoteXY.cutDownTimeEdit, COUNT_OF(previousCutDownTimeEdit));
}


void checkCutdown() {
  if (RemoteXY.testButton == 1) {
    armSwitch();
    return;
  }
  if (!cutDownTimeInitialized || !currentTimeInitialized) {
    disarmSwitch();
    return;
  }

  const int32_t currentTime_s = millis() / 1000 + offset_s;
  if (lowPower) {
    if (currentTime_s < cutDownTime_s) {
      Serial.print(RemoteXY.cutDownTimeEdit);
      Serial.print(" ");
      Serial.println(cutDownTime_s - currentTime_s);
    }
  }
  if (currentTime_s > cutDownTime_s && currentTime_s < cutDownTime_s + getBurnDuration_s()) {
    armSwitch();
    esp_sleep_enable_timer_wakeup(1 * 1000 * 1000);
  } else {
    disarmSwitch();
    esp_sleep_enable_timer_wakeup(5 * 1000 * 1000);
  }
}

void armSwitch() {
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(SWITCH_PIN, HIGH);
  armed = true;
}

void disarmSwitch() {
  digitalWrite(LED_BUILTIN, LOW);
  digitalWrite(SWITCH_PIN, LOW);
  armed = false;
}

uint8_t getBurnDuration_s() {
  return RemoteXY.burnDurationSlider + 5;
}
