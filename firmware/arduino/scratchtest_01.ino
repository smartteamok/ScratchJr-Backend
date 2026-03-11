#include <SoftwareSerial.h>
#include <Adafruit_NeoPixel.h>

#define PIN 13
#define NUMPIXELS 2
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);
SoftwareSerial BT1(9, 8);

uint8_t secuencia[30]; 
int cantidad = 0;
unsigned long ultimaVez = 0;

void setup() {
  BT1.begin(9600);
  pixels.begin();
  pixels.show();
}

void mostrarColor(uint8_t opcode) {
  if (opcode == 0x01) aplicar(255, 0, 0);      // Rojo
  else if (opcode == 0x02) aplicar(0, 0, 255); // Azul
  else if (opcode == 0x03) aplicar(255, 255, 0); // Amarillo
  else if (opcode == 0x04) aplicar(255, 255, 255); // Blanco
  else if (opcode == 0x05) aplicar(128, 0, 128); // Púrpura
}

void aplicar(uint8_t r, uint8_t g, uint8_t b) {
  for(int i=0; i<NUMPIXELS; i++) pixels.setPixelColor(i, pixels.Color(r, g, b));
  pixels.show();
}

void loop() {
  if (BT1.available()) {
    uint8_t dato = BT1.read();

    if (dato == 0xF0) { // EJECUTAR
      for (int i = 0; i < cantidad; i++) {
        mostrarColor(secuencia[i]);
        delay(600);
        pixels.clear(); pixels.show();
        delay(200);
      }
    } 
    else if (dato >= 0x01 && dato <= 0x05) {
      // Si pasó más de 1.5 seg, asumimos que es una secuencia nueva
      if (millis() - ultimaVez > 1500) {
        cantidad = 0; 
      }
      if (cantidad < 30) {
        secuencia[cantidad] = dato;
        cantidad++;
      }
      ultimaVez = millis();
      // Feedback visual rápido (gris) para saber que recibió
      aplicar(10, 10, 10); delay(50); pixels.clear(); pixels.show();
    }
  }
}
