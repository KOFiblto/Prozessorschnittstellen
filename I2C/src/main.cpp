#include <Arduino.h>
#include <Wire.h>

const int I2C_SLAVE_ADDRESS = 0x27;

void sendI2CData() {
  Wire.beginTransmission(I2C_SLAVE_ADDRESS);
  Wire.write('H');
  Wire.endTransmission();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  sendI2CData();
}

void loop() {}