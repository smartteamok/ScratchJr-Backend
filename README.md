# ScratchJr BLE Platform

Este proyecto permite controlar múltiples placas de forma simultánea (hasta 2 Arduino Nano Educabot y 2 BBC micro:bit V2) utilizando protocolos de Bluetooth Low Energy (BLE). La plataforma permite cargar secuencias de instrucciones en la memoria de cada placa y ejecutarlas sincronizadamente mediante un comando maestro de START, incluyendo comunicación bidireccional en tiempo real.

## Estructura del Proyecto

* **/firmware**: Contiene los archivos `.ino` para Arduino y el código JavaScript para micro:bit.
* **test_ble.py**: Aplicación para macOS/Windows con interfaz gráfica en cuadrícula (2x2) basada en la librería Bleak y Tkinter. Incluye indicadores visuales de recepción de datos.
* **index.html**: Versión web optimizada para dispositivos móviles (iOS/Android) utilizando Web Bluetooth API.

## Instalacion de Firmwares

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
3. Utilizar los botones de escaneo para detectar las placas. Conectar cada dispositivo individualmente en su panel correspondiente antes de programar las secuencias.

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

El sistema utiliza el envío de bytes individuales para minimizar la latencia y asegurar la compatibilidad.

| Accion | Opcode (Hex) | Arduino (NeoPixels) | micro:bit (Pantalla) |
| --- | --- | --- | --- |
| **Config: 1** | `0x01` | Rojo | Corazón |
| **Config: 2** | `0x02` | Azul | Cuadrado |
| **Config: 3** | `0x03` | Amarillo | Triángulo |
| **Config: 4** | `0x04` | Blanco | Check |
| **Config: 5** | `0x05` | Púrpura | Cruz |
| **Config: Mensaje** | `0x06` | Envía notificación (`0xAA`) | Envía notificación (`0xAA`) |
| **START** | **`0xF0`** | Ejecuta secuencia en memoria | Ejecuta secuencia en memoria |

### Logica de Secuencia y Memoria

El sistema ya no ejecuta instrucciones de forma inmediata, sino que funciona como una grabadora de secuencias:

1. **Configuración**: Al recibir opcodes de configuración (`0x01` a `0x06`), las placas almacenan los comandos en un array interno. Si transcurre más de 1.5 segundos sin recibir nuevos comandos, el sistema asume que la siguiente instrucción pertenece a una secuencia nueva y vacía la memoria anterior.
2. **Ejecución**: Al recibir el opcode de START (`0xF0`), la placa recorre su array interno y ejecuta cada paso almacenado con un intervalo de tiempo definido, respetando la coreografía programada.

### Comunicacion Bidireccional (Eventos)

Si la secuencia programada incluye el opcode `0x06`, la placa no realizará una acción visual en ese paso (más allá de un tenue feedback de proceso), sino que transmitirá el byte `0xAA` (170 en decimal) de regreso al backend a través de Bluetooth.

El backend en Python intercepta esta notificación e identifica la dirección MAC de origen, encendiendo el LED indicador correspondiente en la interfaz gráfica durante 1 segundo. Esto permite simular un sistema de disparo de eventos y mensajes entre el hardware y el software.

## Notas Tecnicas

* **Pantalla micro:bit**: Muestra una cara recta (Asleep) cuando no hay conexión Bluetooth. Al establecer el vínculo con el dispositivo de control, la pantalla se limpia automáticamente.
* **Seguridad**: Web Bluetooth requiere estrictamente que el sitio web sea servido a través de HTTPS para funcionar.
* **Conectividad**: Los dispositivos BLE solo permiten una conexión activa a la vez. Si una placa no es detectada, verificar que no esté vinculada a otro dispositivo o aplicación.
