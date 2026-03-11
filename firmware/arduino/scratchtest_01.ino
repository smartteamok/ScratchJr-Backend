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
  if (opcode == 0x01) aplicar(255, 0, 0);      
  else if (opcode == 0x02) aplicar(0, 0, 255); 
  else if (opcode == 0x03) aplicar(255, 255, 0); 
  else if (opcode == 0x04) aplicar(255, 255, 255); 
  else if (opcode == 0x05) aplicar(128, 0, 128); 
}

void aplicar(uint8_t r, uint8_t g, uint8_t b) {
  for(int i=0; i<NUMPIXELS; i++) pixels.setPixelColor(i, pixels.Color(r, g, b));
  pixels.show();
}

void loop() {
  if (BT1.available()) {
    uint8_t dato = BT1.read();

    // --- 1. MODO EJECUCIÓN (START) ---
    if (dato == 0xF0) { 
      for (int i = 0; i < cantidad; i++) {
        uint8_t paso_actual = secuencia[i];

        if (paso_actual == 0x06) {
          // Si el paso es el mensaje, se envía a la Mac
          BT1.write(0xAA); 
          // Pequeño feedback visual (azul muy débil) para que veas el "paso"
          aplicar(0, 0, 20); delay(100); pixels.clear(); pixels.show();
          delay(500); // Mantenemos el "ritmo" de 600ms por paso
        } 
        else {
          // Si es un color normal
          mostrarColor(paso_actual);
          delay(600);
          pixels.clear(); pixels.show();
        }
        delay(200); // Pausa entre pasos
      }
    } 
    // --- 2. MODO CONFIGURACIÓN (Guardar en memoria) ---
    // AHORA INCLUYE EL 0x06 COMO UN COMANDO GUARDABLE (0x01 al 0x06)
    else if (dato >= 0x01 && dato <= 0x06) {
      if (millis() - ultimaVez > 1500) {
        cantidad = 0; 
      }
      if (cantidad < 30) {
        secuencia[cantidad] = dato;
        cantidad++;
      }
      ultimaVez = millis();
      // Destello gris de guardado exitoso
      aplicar(10, 10, 10); delay(50); pixels.clear(); pixels.show();
    }
  }
}