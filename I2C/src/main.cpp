#include <Arduino.h>

const uint8_t I2C_SLAVE_ADDRESS = 0x27;

void sendI2CData() {
  // START
  TWCR = (1 << TWINT) | (1 << TWSTA) | (1 << TWEN);
  while (!(TWCR & (1 << TWINT)));

  // Adresse und Read/Write Bit (0 = Write)
  TWDR = (I2C_SLAVE_ADDRESS << 1);
  TWCR = (1 << TWINT) | (1 << TWEN);
  while (!(TWCR & (1 << TWINT)));

  // Gesendeter Datenwert ('H')
  TWDR = 'H';
  TWCR = (1 << TWINT) | (1 << TWEN);
  while (!(TWCR & (1 << TWINT)));

  // STOP
  TWCR = (1 << TWINT) | (1 << TWEN) | (1 << TWSTO);
}

void setup() {
  // UART begin(115200) - Double transmission speed for 115200 baud @ 16 MHz
  UCSR0A = (1 << U2X0); // Aktiviert die doppelte Übertragungsgeschwindigkeit.
  UBRR0H = 0;
  UBRR0L = 16; // Baudrate auf 115200 bei 16 MHz Taktfrequenz.
  UCSR0B = (1 << TXEN0) | (1 << RXEN0); // Aktiviert TX und RX.
  UCSR0C = (1 << UCSZ01) | (1 << UCSZ00); // Setzt das Datenformat auf 8-Bit.

  // I2C begin() - 100 kHz at 16 MHz
  TWSR = 0x00;        // Prescaler 1
  TWBR = 72;          // Bit rate register
  TWCR = (1 << TWEN); // Enable TWI

  sendI2CData();
}

void loop() {}