# ScratchJr BLE Platform

Este proyecto permite controlar un Arduino Nano (Educabot) y una BBC micro:bit V2 de forma simultánea (1:m) utilizando protocolos de Bluetooth Low Energy (BLE). La plataforma permite cargar una instrucción y ejecutarla mediante un comando maestro de START.

## Estructura del Proyecto

* **/firmware**: Contiene los archivos `.ino` para Arduino y el código JavaScript para micro:bit.
* **test_ble.py**: Aplicación para macOS/Windows con interfaz gráfica basada en la librería Bleak y Tkinter.
* **index.html**: Versión web optimizada para dispositivos móviles (iOS/Android) utilizando Web Bluetooth API.

## Instalación de Firmwares

Los archivos necesarios se encuentran en la carpeta `/firmware`:

1. **Arduino**: Subir el código utilizando Arduino IDE. Requiere la librería `Adafruit_NeoPixel`. Configurado para 2 píxeles en el pin 13.
2. **micro:bit**: Copiar el código en el editor de [MakeCode](https://makecode.microbit.org) y transferirlo a la placa. El servicio UART debe estar activo.

## Camino 1: Uso Local (Python en Mac/PC)

Sistema de control desde computadora de escritorio utilizando la antena Bluetooth interna.

### Requisitos

* Python 3.10 o superior.
* Instalación de dependencias: `pip install bleak`.

### Ejecución

1. Abrir la terminal en el directorio del proyecto.
2. Ejecutar: `python test_ble.py`.
3. Utilizar el botón de escaneo para detectar las placas. Conectar cada dispositivo individualmente desde la lista antes de enviar comandos.

## Camino 2: Uso desde Navegador (Móvil / Tablet)

Control directo desde el chip Bluetooth del dispositivo móvil hacia las placas mediante una interfaz web.

### iOS (iPhone / iPad Mini 5)

Safari y Chrome en iOS no soportan Web Bluetooth API por restricciones del sistema operativo.

1. Instalar el navegador **Bluefy - Web Browser** desde la App Store.
2. Alojar el archivo `index.html` en un servidor con protocolo **HTTPS** (ejemplo: GitHub Pages).
3. Abrir la URL en Bluefy.
4. Presionar el botón de conexión para abrir el selector nativo de iOS.

### Android

1. Utilizar el navegador **Google Chrome**.
2. Activar Bluetooth y Ubicación (GPS) en los ajustes del sistema.
3. Acceder a la URL del proyecto (requiere HTTPS).

## Protocolo de Comunicacion (Opcodes)

El sistema utiliza el envío de bytes individuales para minimizar la latencia y asegurar la compatibilidad entre plataformas.

| Accion | Opcode (Hex) | Arduino (NeoPixels) | micro:bit (Pantalla) |
| --- | --- | --- | --- |
| **Config: 1** | `0x01` | Rojo | Corazón |
| **Config: 2** | `0x02` | Azul | Cuadrado |
| **Config: 3** | `0x03` | Amarillo | Triángulo |
| **Config: 4** | `0x04` | Blanco | Check |
| **Config: 5** | `0x05` | Púrpura | Cruz |
| **START** | **`0xF0`** | Ejecuta color guardado | Ejecuta icono guardado |

### Logica de Sobrescritura

Al recibir un nuevo opcode de configuración (`0x01` a `0x05`), las placas eliminan la instrucción previa y almacenan la nueva. Si transcurre más de 1.5 segundos entre comandos, el sistema asume que se trata de una nueva sesión de configuración.

## Notas Tecnicas

* **Pantalla micro:bit**: Muestra una cara recta (Asleep) cuando no hay conexión Bluetooth. Al establecer el vínculo con la Mac o el iPad, la pantalla se limpia automáticamente.
* **Seguridad**: Web Bluetooth requiere estrictamente que el sitio web sea servido a través de HTTPS para funcionar.
* **Conectividad**: Los dispositivos BLE solo permiten una conexión activa a la vez. Si una placa no es detectada, verificar que no esté vinculada a otro dispositivo o aplicación.
