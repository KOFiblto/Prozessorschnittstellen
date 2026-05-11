#include <Arduino.h>

void setup() {
  // Set SS (PB2), MOSI (PB3), and SCK (PB5) as output
  DDRB |= (1 << PB2) | (1 << PB3) | (1 << PB5);
  // SS HIGH
  PORTB |= (1 << PB2);
  
  // Enable SPI, Master, set clock rate fck/4 (4 MHz at 16 MHz)
  SPCR = (1 << SPE) | (1 << MSTR);

  // SS LOW
  PORTB &= ~(1 << PB2);
  
  // Transfer 'H'
  SPDR = 'H';
  while (!(SPSR & (1 << SPIF)));
  
  // SS HIGH
  PORTB |= (1 << PB2);
}

void loop() {}
