#include <ESP32Servo.h>
#include "position.hpp"

PositionEstimator* estimator = nullptr;
byte estimatorMemory[sizeof(PositionEstimator)];

Servo elevonServo;
// Pilot's left and right
Servo leftAileronServo;
Servo rightAileronServo;

void setup(void) {
  Serial.begin(115200);

  // Dynamically allocating this normally gives me a "heap != NULL && "free() target pointer is
  // outside heap areas"... I must be doing something wrong. Anyway, placement new works.
  estimator = new (estimatorMemory) PositionEstimator();

  elevonServo.attach(19);
  elevonServo.write(90);
  delay(10000);
}

void loop() {
  estimator->update();
  const Position position = estimator->get();
  if (position.valid && position.updated) {
    Serial.printf("%.4f %.4f %.1fm\n", position.latitude_d, position.longitude_d, position.altitude_m);
  }
  Serial.printf("pitch:%.1f roll:%.1f yaw:%.1f\n", position.pitch_d, position.roll_d, position.yaw_d);

  const float elevonAngle = constrain(-position.pitch_d, -45, 45) + 90;
  elevonServo.write(angle);
  Serial.printf("elevon:%.1f\n", angle);

  const float aileronServo = constrain(-position.roll_d, -45, 45) + 90;
  leftAileronServo.write(angle);
  rightAileronServo.write(angle);
  Serial.printf("aileron:%.1f\n", angle);
}
