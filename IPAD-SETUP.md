# Cómo ejecutar la app BLE en iPad con Bluefy

## Requisitos

- **iPad** (iPad Mini 5 u otro compatible)
- **Bluefy** instalado desde la App Store: [Bluefy - Web BLE Browser](https://apps.apple.com/us/app/bluefy-web-ble-browser/id1492822055)
- La placa micro:bit o Arduino/Educabot con firmware BLE encendida

## Método 1: GitHub Pages (recomendado)

Si el proyecto está subido a GitHub y tienes GitHub Pages activado:

1. **Sube el repo** a GitHub (ver instrucciones abajo).
2. En el repo: **Settings** → **Pages** → Source: **Deploy from a branch** → Branch: **main** (o master) → **Save**.
3. En el iPad, abre **Bluefy** y ve a:
   ```
   https://TU_USUARIO.github.io/ScratchJr-Backend/
   ```
   (sustituye `TU_USUARIO` por tu usuario de GitHub)

La URL es HTTPS, así que Bluefy debería funcionar bien. El sitio tarda 1–2 minutos en publicarse la primera vez.

## Método 2: Servidor local en tu red

Bluefy requiere **HTTPS** para cargar páginas remotas. Si usas un servidor local por HTTP, Bluefy puede cargar la URL si está en tu red local.

1. En tu Mac (o PC en la misma red), levanta un servidor en la carpeta del proyecto:

   ```bash
   cd /ruta/a/ScratchJr-Backend
   python3 -m http.server 8080
   ```

2. Obtén la IP de tu Mac:
   - `ifconfig | grep "inet "` (busca la IP, ej. 192.168.1.10)

3. En el iPad, abre **Bluefy** y en la barra de direcciones escribe:
   ```
   http://192.168.1.10:8080/scratchjr-ble-app.html
   ```
   (sustituye la IP por la de tu Mac)

4. Nota: Bluefy puede exigir HTTPS para ciertas APIs. Si da error, usa el método 2.

## Método 3: HTTPS con ngrok

Si Bluefy rechaza HTTP:

1. Instala [ngrok](https://ngrok.com/): `brew install ngrok`

2. Levanta el servidor local:
   ```bash
   python3 -m http.server 8080
   ```

3. En otra terminal:
   ```bash
   ngrok http 8080
   ```

4. ngrok te dará una URL pública HTTPS (ej. `https://abc123.ngrok-free.app`). En Bluefy entra a:
   ```
   https://abc123.ngrok-free.app/scratchjr-ble-app.html
   ```

## Método 4: Archivo local (si Bluefy lo permite)

Algunas versiones de Bluefy permiten abrir archivos locales:

1. Copia `scratchjr-ble-app.html` al iPad (AirDrop, iCloud Drive, etc.).
2. Abre el archivo con Bluefy si tiene opción “Abrir con”.

## Uso

1. Toca **Conectar dispositivo** (debe ser un gesto de usuario para activar BLE).
2. Selecciona tu micro:bit o Arduino/Educabot en el selector del sistema.
3. Una vez conectado, usa **START** y los paneles de programación 1 y 2 igual que en la app de Mac.
4. Para conectar otro dispositivo, toca **Conectar dispositivo** de nuevo.

## Subir a GitHub

Si aún no tienes el repo en GitHub:

```bash
cd /Users/marianobat/dev/ScratchJr-Backend

# Inicializar git
git init
git add .
git commit -m "ScratchJr BLE: app Mac + app web iPad"

# Crear repo en GitHub (en github.com: New repository → ScratchJr-Backend)
# Luego enlaza y sube:
git remote add origin https://github.com/TU_USUARIO/ScratchJr-Backend.git
git branch -M main
git push -u origin main
```

Después activa GitHub Pages en **Settings → Pages** del repo.

## Soporte Web Bluetooth en iOS

Safari en iOS **no soporta** Web Bluetooth nativamente. Bluefy implementa la API Web Bluetooth para que puedas usar la misma app web en iPad.
