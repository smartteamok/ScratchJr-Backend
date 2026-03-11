# ScratchJr BLE Backend

Panel de control BLE para ScratchJr: conecta micro:bit y Arduino/Educabot vía Bluetooth Low Energy.

## Contenido

- **`test_ble.py`** — App de escritorio (Mac) con tkinter + Bleak
- **`scratchjr-ble-app.html`** — App web para iPad (Web Bluetooth API, usar con [Bluefy](https://apps.apple.com/app/bluefy-web-ble-browser/id1492822055))
- **`IPAD-SETUP.md`** — Instrucciones para ejecutar en iPad

## Uso en iPad

Si este repo está publicado en GitHub Pages:

1. Instala **Bluefy** desde la App Store.
2. Abre en Bluefy: `https://TU_USUARIO.github.io/ScratchJr-Backend/`
3. Pulsa **Conectar dispositivo** y selecciona tu micro:bit o Arduino.

## Uso en Mac

```bash
pip install bleak
python test_ble.py
```
