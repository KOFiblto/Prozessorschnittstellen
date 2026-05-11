# Prozessorschnittstellen: I2C, SPI & UART

Dieses Repository enthält die Implementierung der Kommunikationsschnittstellen I2C, SPI und UART auf einem Arduino Uno R3 (ATmega328P). Die Schnittstellen wurden in zwei verschiedenen Versionen umgesetzt:

## Versionen
- **V1.x (Arduino Libraries):** Nutzt die Standard-Arduino-Bibliotheken (`Wire.h`, `SPI.h`, `Serial`).
- **V2.x (Register-Level):** Verwendet bare-metal C-Code zur direkten Manipulation der Mikrocontroller-Register (z.B. `TWCR`, `SPCR`, `UCSR0A`).

## Projektstruktur
Das Repository ist in drei Hauptordner unterteilt:
- `/I2C/`
- `/SPI/`
- `/UART/`

Jeder dieser Ordner repräsentiert ein eigenständiges Projekt und enthält die jeweiligen Cpp-Quellcodes in `/src/main.cpp`.

## Wokwi Simulation
Die Projekte sind für die Simulation in Wokwi vorbereitet:
- **`wokwi.toml`**: Konfigurationsdatei des Wokwi-Projekts.
- **`diagram.json`**: Beschreibt den Aufbau und die Verdrahtung der Bauteile.
- **VCD-Datei (.vcd):** Value Change Dump Datei, die vom Logic Analyzer exportiert wird, die die Flanken bzw Signale enthält.

## Git Tags
Die Entwicklungsstände sind über folgende Git Tags markiert:
- `I2C-V2` / `I2C-V1.x`
- `SPI-V2` / `SPI-V1.x`
- `UART-V2` / `UART-V1.x`

Mit `git checkout <tag>` kann zwischen den Library-basierten und Register-Level Versionen gewechselt werden.
