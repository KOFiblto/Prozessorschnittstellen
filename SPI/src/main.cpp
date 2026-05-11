#include <Arduino.h>
#include <SPI.h>

void setup() {
  pinMode(SS, OUTPUT);
  digitalWrite(SS, HIGH);
  
  SPI.begin();
  SPI.beginTransaction(SPISettings(4000000, MSBFIRST, SPI_MODE0));

  digitalWrite(SS, LOW);
  SPI.transfer('H');
  digitalWrite(SS, HIGH);
  
  SPI.endTransaction();
}

void loop() {}