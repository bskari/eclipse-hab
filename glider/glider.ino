#include "position.hpp"

PositionEstimator* estimator = nullptr;
byte estimatorMemory[sizeof(PositionEstimator)];

void setup(void) {
  Serial.begin(115200);
  Serial.println("Glider test");
  // Dynamically allocating this normally gives me a "heap != NULL && "free() target pointer is
  // outside heap areas"... I must be doing something wrong.
  estimator = new (estimatorMemory) PositionEstimator();
}

void loop() {
  estimator->update();
  const Position position = estimator->get();
  if (position.valid) {
    Serial.printf("%f %f %fm\n", position.latitude_d, position.longitude_d, position.altitude_m);
  }
  Serial.printf("pitch:%f roll:%f yaw:%f\n", position.pitch_d, position.roll_d, position.yaw_d);
  delay(500);
}
