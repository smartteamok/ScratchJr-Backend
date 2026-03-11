import asyncio
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from bleak import BleakScanner, BleakClient

# --- CONFIGURACIÓN DE UUIDs ---
# Comando START: 0xF0 (no es opcode de programación 1 ni 2, que usan 0x01-0x05)
OPCODE_START = 0xF0

UUID_ARDUINO = "0000ffe1-0000-1000-8000-00805f9b34fb"
UUID_MB_LEER = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_MB_ESCRIBIR = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# Diccionarios globales para manejar el estado
dispositivos_encontrados = {} # Guarda la dirección MAC -> Objeto BleakDevice
clientes_activos = {}         # Guarda la dirección MAC -> (BleakClient, UUID_Escritura, Nombre)

def log_gui(mensaje):
    """Imprime en la terminal y en la ventanita de la app"""
    print(mensaje)
    if 'txt_log' in globals():
        txt_log.insert(tk.END, mensaje + "\n")
        txt_log.see(tk.END)

async def manejar_mensajes(sender, data):
    mensaje = data.decode('utf-8', errors='ignore').strip()
    log_gui(f"📥 [RECIBIDO] {mensaje}")

async def enviar_comando_start():
    """Envía el opcode START (0xF0) a todas las placas conectadas. Micro:bit recibe 0xF0\\n."""
    if not clientes_activos:
        log_gui("⚠️ No hay placas conectadas para enviar START.")
        return
    for mac, (client, uuid_escritura, nombre) in clientes_activos.items():
        payload = bytes([OPCODE_START]) + (b"\n" if uuid_escritura == UUID_MB_ESCRIBIR else b"")
        try:
            await client.write_gatt_char(uuid_escritura, payload, response=False)
            log_gui(f"📤 [ENVIADO a {nombre}] -> START (0xF0)")
        except Exception as e:
            log_gui(f"❌ Falló el envío a {nombre}: {e}")


async def enviar_comando_ble(texto):
    """Envía un texto a todas las placas conectadas a la vez"""
    if not clientes_activos:
        log_gui("⚠️ No hay placas conectadas para enviar mensajes.")
        return

    data = (texto + "\n").encode("utf-8")
    for mac, (client, uuid_escritura, nombre) in clientes_activos.items():
        try:
            await client.write_gatt_char(uuid_escritura, data, response=False)
            log_gui(f"📤 [ENVIADO a {nombre}] -> {texto}")
        except Exception as e:
            log_gui(f"❌ Falló el envío a {nombre}: {e}")


async def enviar_a_microbit(data_bytes: bytes):
    """Envía bytes solo a dispositivos micro:bit. Añade \\n al final."""
    destinos = [
        (mac, client, uuid_escritura, nombre)
        for mac, (client, uuid_escritura, nombre) in clientes_activos.items()
        if uuid_escritura == UUID_MB_ESCRIBIR
    ]
    if not destinos:
        log_gui("⚠️ No hay micro:bit conectado para programación 1.")
        return
    payload = data_bytes + b"\n"
    for mac, client, uuid_escritura, nombre in destinos:
        try:
            await client.write_gatt_char(uuid_escritura, payload, response=False)
            log_gui(f"📤 [ENVIADO a {nombre}] -> {data_bytes.hex().upper()}")
        except Exception as e:
            log_gui(f"❌ Falló el envío a {nombre}: {e}")


async def enviar_a_arduino(data_bytes: bytes):
    """Envía bytes solo a dispositivos Arduino"""
    destinos = [
        (mac, client, uuid_escritura, nombre)
        for mac, (client, uuid_escritura, nombre) in clientes_activos.items()
        if uuid_escritura == UUID_ARDUINO
    ]
    if not destinos:
        log_gui("⚠️ No hay Arduino conectado para programación 2.")
        return
    for mac, client, uuid_escritura, nombre in destinos:
        try:
            await client.write_gatt_char(uuid_escritura, data_bytes, response=False)
            log_gui(f"📤 [ENVIADO a {nombre}] -> {data_bytes.hex().upper()}")
        except Exception as e:
            log_gui(f"❌ Falló el envío a {nombre}: {e}")

# --- LÓGICA DE ESCANEO Y CONEXIÓN ---
async def escanear_dispositivos():
    log_gui("🔍 Buscando dispositivos Bluetooth (5 segundos)...")
    btn_scan.config(state=tk.DISABLED)
    lista_dispositivos.delete(0, tk.END)
    dispositivos_encontrados.clear()
    
    # Escaneamos el aire
    devices = await BleakScanner.discover(timeout=5.0)
    
    for d in devices:
        # Filtramos para que solo muestre dispositivos con nombre
        if d.name and d.name != "Unknown":
            dispositivos_encontrados[d.address] = d
            # Agregamos a la lista visual de la interfaz
            lista_dispositivos.insert(tk.END, f"{d.address} | {d.name}")
            
    log_gui(f"✅ Escaneo terminado. Se encontraron {len(dispositivos_encontrados)} dispositivos.")
    btn_scan.config(state=tk.NORMAL)

async def conectar_seleccionado(address):
    if address in clientes_activos:
        log_gui("⚠️ Ya estás conectado a esta placa.")
        return
        
    device = dispositivos_encontrados.get(address)
    if not device: return
    
    log_gui(f"⏳ Conectando a {device.name} ({address})...")
    
    try:
        client = BleakClient(device)
        await client.connect()
        
        es_microbit = False
        es_arduino = False
        
        # MAGIA DE AUTODETECCIÓN: Revisamos qué servicios tiene la placa por dentro
        for service in client.services:
            for char in service.characteristics:
                if char.uuid == UUID_MB_ESCRIBIR:
                    es_microbit = True
                elif char.uuid == UUID_ARDUINO:
                    es_arduino = True

        # La configuramos dependiendo de lo que encontramos
        if es_microbit:
            log_gui(f"🚀 ¡CONECTADO a {device.name} (Modo micro:bit)!")
            clientes_activos[address] = (client, UUID_MB_ESCRIBIR, device.name)
            await client.start_notify(UUID_MB_LEER, manejar_mensajes)
            
        elif es_arduino:
            log_gui(f"🚀 ¡CONECTADO a {device.name} (Modo Arduino)!")
            clientes_activos[address] = (client, UUID_ARDUINO, device.name)
            await client.start_notify(UUID_ARDUINO, manejar_mensajes)
            
        else:
            log_gui(f"❌ {device.name} no es compatible. Desconectando...")
            await client.disconnect()
            return

        # Mantenemos viva la conexión de esta placa
        while client.is_connected:
            await asyncio.sleep(1)
            
        log_gui(f"⚠️ {device.name} se ha desconectado físicamente.")
        
    except Exception as e:
        log_gui(f"❌ Error al conectar con {device.name}: {e}")
    finally:
        if address in clientes_activos:
            del clientes_activos[address]

# --- EVENTOS DE LA INTERFAZ GRÁFICA ---
def click_scan():
    asyncio.create_task(escanear_dispositivos())

def click_connect():
    seleccion = lista_dispositivos.curselection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Por favor selecciona un dispositivo de la lista primero.")
        return
    
    # Extraemos la dirección MAC del texto seleccionado (lo que está antes del "|")
    texto_seleccionado = lista_dispositivos.get(seleccion[0])
    address = texto_seleccionado.split(" | ")[0]
    
    asyncio.create_task(conectar_seleccionado(address))

def click_start():
    log_gui("▶ Botón START presionado (envía 0xF0)")
    asyncio.create_task(enviar_comando_start())


def crear_panel_programacion(parent, titulo, botones_config, enviar_fn):
    """Crea un panel de programación con toggles y cuadro hex.
    botones_config: lista de (texto, byte_value) ej: [("♥", 0x01), ("□", 0x02), ...]
    enviar_fn: async function(bytes) para enviar
    """
    frame = tk.LabelFrame(parent, text=titulo, padx=8, pady=8)
    frame.pack(pady=8, padx=10, fill=tk.X)

    # Estado: set de bytes actualmente activos (orden de botones 1-5)
    estados = {i: tk.BooleanVar(value=False) for i in range(5)}

    def actualizar_hex():
        bytes_activos = [
            botones_config[i][1]
            for i in range(5)
            if estados[i].get()
        ]
        hex_str = "".join(f"{b:02X}" for b in bytes_activos)
        hex_display.config(text=hex_str or "-")

    # Fila: cuadro hex + botones toggle + enviar
    fila = tk.Frame(frame)
    fila.pack(fill=tk.X)

    hex_display = tk.Label(fila, text="-", font=("Courier", 12), width=20, relief=tk.SUNKEN)
    hex_display.pack(side=tk.LEFT, padx=(0, 10))

    for i, (texto, byte_val) in enumerate(botones_config):
        cb = tk.Checkbutton(
            fila,
            text=texto,
            variable=estados[i],
            indicatoron=False,
            selectcolor="lightblue",
            command=actualizar_hex,
            font=("Arial", 10),
            width=3,
        )
        cb.pack(side=tk.LEFT, padx=2)

    def click_enviar_panel():
        bytes_activos = [
            botones_config[i][1]
            for i in range(5)
            if estados[i].get()
        ]
        if not bytes_activos:
            log_gui("⚠️ No hay bytes seleccionados para enviar.")
            return
        data = bytes(bytes_activos)
        asyncio.create_task(enviar_fn(data))

    tk.Button(fila, text="Enviar", command=click_enviar_panel).pack(side=tk.LEFT, padx=10)
    return frame


async def mantener_gui_viva(root):
    while True:
        root.update()
        await asyncio.sleep(0.01)

async def main():
    global txt_log, lista_dispositivos, btn_scan
    
    # --- CREACIÓN DE LA VENTANA ---
    root = tk.Tk()
    root.title("Plataforma BLE - ScratchJr Backend")
    root.geometry("650x680")
    
    # Panel Superior: Escaneo y Conexión
    frame_lista = tk.Frame(root)
    frame_lista.pack(pady=10, fill=tk.X, padx=10)
    
    btn_scan = tk.Button(frame_lista, text="1. 🔍 Escanear Bluetooth", command=click_scan)
    btn_scan.pack(side=tk.LEFT, padx=5)
    
    btn_conectar = tk.Button(frame_lista, text="2. 🔗 Conectar Seleccionado", command=click_connect)
    btn_conectar.pack(side=tk.RIGHT, padx=5)
    
    # Cuadro de lista para los dispositivos
    lista_dispositivos = tk.Listbox(root, height=6)
    lista_dispositivos.pack(fill=tk.X, padx=15, pady=5)
    
    # Panel Medio: START y dos secciones de programación
    frame_start = tk.Frame(root)
    frame_start.pack(pady=8)
    tk.Button(frame_start, text="▶ START", bg="lightgreen", command=click_start).pack()

    # Programación 1: micro:bit — ♥ □ △ ✓ ✗
    crear_panel_programacion(
        root,
        "Programación 1 (micro:bit)",
        [("♥", 0x01), ("□", 0x02), ("△", 0x03), ("✓", 0x04), ("✗", 0x05)],
        enviar_a_microbit,
    )

    # Programación 2: Arduino — R B Y W P
    crear_panel_programacion(
        root,
        "Programación 2 (Arduino)",
        [("R", 0x01), ("B", 0x02), ("Y", 0x03), ("W", 0x04), ("P", 0x05)],
        enviar_a_arduino,
    )
    
    # Panel Inferior: Status / Log
    tk.Label(root, text="Status", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10)
    txt_log = ScrolledText(root, width=70, height=12)
    txt_log.pack(pady=5, padx=10)
    
    log_gui("👋 ¡Bienvenido! Haz clic en Escanear para empezar.")
    
    # Arrancamos la interfaz asíncrona
    await mantener_gui_viva(root)

if __name__ == "__main__":
    asyncio.run(main())