#include <Arduino.h>
#include <util/delay.h>

void setup() {
  // Serial.begin(115200) @ 16MHz, Double transmission speed
  UCSR0A = (1 << U2X0);
  UBRR0H = 0;
  UBRR0L = 16;
  UCSR0B = (1 << TXEN0) | (1 << RXEN0);
  UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);

  _delay_ms(100); 

  // Serial.print('H')
  while (!(UCSR0A & (1 << UDRE0))); // wait for empty transmit buffer
  UDR0 = 'H';
}

void loop() {}