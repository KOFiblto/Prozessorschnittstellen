#include <Arduino.h>
#include <SPI.h>

const int CS_PIN = 10;

void setup() {
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  SPI.begin();
}

void sendSPIData() {
  const char *message = "Hello World";

  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_PIN, LOW);

  for (int i = 0; message[i] != '\0'; i++) {
    SPI.transfer(message[i]);
  }

  digitalWrite(CS_PIN, HIGH);
  SPI.endTransaction();
}

void loop() {
  sendSPIData();
  delay(1000);
}