#include <Arduino.h>
#include <Wire.h>

const int I2C_SLAVE_ADDRESS = 0x68;

void setup() {
  Serial.begin(115200);
  Wire.begin();
}

void sendI2CData() {
  Wire.beginTransmission(I2C_SLAVE_ADDRESS);
  Wire.write("Hello World");
  Wire.endTransmission();
}

void loop() {
  sendI2CData();
  delay(1000);
}