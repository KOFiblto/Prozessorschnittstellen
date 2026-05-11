#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(100); 
  Serial.print('H');
}

void loop() {}