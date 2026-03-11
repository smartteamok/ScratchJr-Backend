import asyncio
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from bleak import BleakScanner, BleakClient

# --- CONFIGURACIÓN DE UUIDs ---
OPCODE_START = 0xF0
OPCODE_MENSAJE = 0x06

UUID_ARDUINO = "0000ffe1-0000-1000-8000-00805f9b34fb"
UUID_MB_LEER = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_MB_ESCRIBIR = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# Diccionarios globales
dispositivos_encontrados = {}
# clientes_activos[mac] = (client, uuid_escritura, nombre, tipo, slot, program_index)
# program_index: 0=microbit1, 1=arduino1, 2=microbit2, 3=arduino2
clientes_activos = {}
led_indicadores = {}  # program_index -> (canvas, circle_id)
root_tk = None  # referencia para root.after()

def log_gui(mensaje):
    """Imprime en la terminal y en la ventanita de la app"""
    print(mensaje)
    if 'txt_log' in globals():
        txt_log.insert(tk.END, mensaje + "\n")
        txt_log.see(tk.END)


def encender_led_programa(program_index: int):
    """Enciende el LED del área program_index durante 1 segundo."""
    if program_index not in led_indicadores or not root_tk:
        return
    canvas, circle_id = led_indicadores[program_index]
    canvas.itemconfig(circle_id, fill="#00ff00")  # verde

    def apagar():
        canvas.itemconfig(circle_id, fill="#666666")

    root_tk.after(1000, apagar)


def make_manejar_mensajes(mac: str):
    """Factory: crea un handler que conoce la MAC del dispositivo."""
    async def handler(sender, data):
        raw = bytes(data) if hasattr(data, "__iter__") else data
        if raw and 0xAA in raw:
            info = clientes_activos.get(mac)
            if info:
                _, _, _, _, _, program_index = info
                encender_led_programa(program_index)
        try:
            mensaje = raw.decode("utf-8", errors="ignore").strip()
            if mensaje:
                log_gui(f"📥 [RECIBIDO] {mensaje}")
        except Exception:
            pass

    return handler

async def enviar_comando_start():
    """Envía el opcode START (0xF0) a todas las placas conectadas."""
    if not clientes_activos:
        log_gui("⚠️ No hay placas conectadas para enviar START.")
        return
    for mac, (client, uuid_escritura, nombre, tipo, *_) in clientes_activos.items():
        payload = bytes([OPCODE_START]) + (b"\n" if tipo == "microbit" else b"")
        try:
            await client.write_gatt_char(uuid_escritura, payload, response=False)
            log_gui(f"📤 [ENVIADO a {nombre}] -> START (0xF0)")
        except Exception as e:
            log_gui(f"❌ Falló el envío a {nombre}: {e}")


async def enviar_a_programa(program_index: int, data_bytes: bytes, add_newline: bool):
    """Envía bytes al dispositivo asignado al área program_index."""
    for mac, (client, uuid_escritura, nombre, tipo, slot, prog_idx) in clientes_activos.items():
        if prog_idx != program_index:
            continue
        payload = data_bytes + (b"\n" if add_newline else b"")
        try:
            await client.write_gatt_char(uuid_escritura, payload, response=False)
            log_gui(f"📤 [ENVIADO a {nombre}] -> {data_bytes.hex().upper()}")
        except Exception as e:
            log_gui(f"❌ Falló el envío a {nombre}: {e}")
        return
    log_gui(f"⚠️ No hay placa conectada en programación {program_index + 1}.")


async def enviar_comando_ble(texto):
    """Envía un texto a todas las placas conectadas a la vez"""
    if not clientes_activos:
        log_gui("⚠️ No hay placas conectadas para enviar mensajes.")
        return
    data = (texto + "\n").encode("utf-8")
    for mac, (client, uuid_escritura, nombre, *_) in clientes_activos.items():
        try:
            await client.write_gatt_char(uuid_escritura, data, response=False)
            log_gui(f"📤 [ENVIADO a {nombre}] -> {texto}")
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

        if not es_microbit and not es_arduino:
            log_gui(f"❌ {device.name} no es compatible. Desconectando...")
            await client.disconnect()
            return

        tipo = "microbit" if es_microbit else "arduino"
        uuid_esc = UUID_MB_ESCRIBIR if es_microbit else UUID_ARDUINO
        uuid_leer = UUID_MB_LEER if es_microbit else UUID_ARDUINO

        mismo_tipo = [m for m, t in clientes_activos.items() if t[3] == tipo]
        slot = len(mismo_tipo)
        if slot >= 2:
            log_gui(f"❌ Ya hay 2 {tipo} conectados. Desconectando...")
            await client.disconnect()
            return

        program_index = slot * 2 + (0 if tipo == "microbit" else 1)
        if es_microbit:
            log_gui(f"🚀 ¡CONECTADO a {device.name} (micro:bit {slot + 1})!")
        else:
            log_gui(f"🚀 ¡CONECTADO a {device.name} (Arduino {slot + 1})!")

        clientes_activos[address] = (client, uuid_esc, device.name, tipo, slot, program_index)
        handler = make_manejar_mensajes(address)
        await client.start_notify(uuid_leer, handler)

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


def crear_panel_programacion(parent, titulo, botones_config, program_index: int, add_newline: bool):
    """Crea un panel con LED, toggles (incl. Mensaje 0x06) y enviar a la placa del program_index."""
    frame = tk.LabelFrame(parent, text=titulo, padx=8, pady=8)
    frame.pack(pady=8, padx=10, fill=tk.X)

    n = len(botones_config)
    estados = {i: tk.BooleanVar(value=False) for i in range(n)}

    def actualizar_hex():
        bytes_activos = [botones_config[i][1] for i in range(n) if estados[i].get()]
        hex_str = "".join(f"{b:02X}" for b in bytes_activos)
        hex_display.config(text=hex_str or "-")

    fila = tk.Frame(frame)
    fila.pack(fill=tk.X)

    # LED indicador
    led_canvas = tk.Canvas(fila, width=20, height=20, highlightthickness=0)
    led_canvas.pack(side=tk.LEFT, padx=(0, 8))
    circle_id = led_canvas.create_oval(2, 2, 18, 18, fill="#666666", outline="#444")
    led_indicadores[program_index] = (led_canvas, circle_id)

    hex_display = tk.Label(fila, text="-", font=("Courier", 12), width=18, relief=tk.SUNKEN)
    hex_display.pack(side=tk.LEFT, padx=(0, 8))

    for i, (texto, _) in enumerate(botones_config):
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
        bytes_activos = [botones_config[i][1] for i in range(n) if estados[i].get()]
        if not bytes_activos:
            log_gui("⚠️ No hay bytes seleccionados para enviar.")
            return
        data = bytes(bytes_activos)
        asyncio.create_task(enviar_a_programa(program_index, data, add_newline))

    tk.Button(fila, text="Enviar", command=click_enviar_panel).pack(side=tk.LEFT, padx=10)
    return frame


async def mantener_gui_viva(root):
    while True:
        root.update()
        await asyncio.sleep(0.01)

async def main():
    global txt_log, lista_dispositivos, btn_scan, root_tk

    root = tk.Tk()
    root_tk = root
    root.title("Plataforma BLE - ScratchJr Backend (4 placas)")
    root.geometry("800x920")

    # Panel Superior: Escaneo y Conexión
    frame_lista = tk.Frame(root)
    frame_lista.pack(pady=10, fill=tk.X, padx=10)

    btn_scan = tk.Button(frame_lista, text="1. 🔍 Escanear Bluetooth", command=click_scan)
    btn_scan.pack(side=tk.LEFT, padx=5)

    btn_conectar = tk.Button(frame_lista, text="2. 🔗 Conectar Seleccionado", command=click_connect)
    btn_conectar.pack(side=tk.RIGHT, padx=5)

    lista_dispositivos = tk.Listbox(root, height=5)
    lista_dispositivos.pack(fill=tk.X, padx=15, pady=5)

    frame_start = tk.Frame(root)
    frame_start.pack(pady=8)
    tk.Button(frame_start, text="▶ START", bg="lightgreen", command=click_start).pack()

    # 4 áreas de programación: microbit1, arduino1, microbit2, arduino2
    prog_configs = [
        ("Programación 1 (micro:bit 1)", [("♥", 0x01), ("□", 0x02), ("△", 0x03), ("✓", 0x04), ("✗", 0x05), ("Msg", OPCODE_MENSAJE)], True),
        ("Programación 2 (Arduino 1)", [("R", 0x01), ("B", 0x02), ("Y", 0x03), ("W", 0x04), ("P", 0x05), ("Msg", OPCODE_MENSAJE)], False),
        ("Programación 3 (micro:bit 2)", [("♥", 0x01), ("□", 0x02), ("△", 0x03), ("✓", 0x04), ("✗", 0x05), ("Msg", OPCODE_MENSAJE)], True),
        ("Programación 4 (Arduino 2)", [("R", 0x01), ("B", 0x02), ("Y", 0x03), ("W", 0x04), ("P", 0x05), ("Msg", OPCODE_MENSAJE)], False),
    ]
    for i, (titulo, botones, add_nl) in enumerate(prog_configs):
        crear_panel_programacion(root, titulo, botones, i, add_nl)
    
    # Panel Inferior: Status / Log
    tk.Label(root, text="Status", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10)
    txt_log = ScrolledText(root, width=70, height=12)
    txt_log.pack(pady=5, padx=10)
    
    log_gui("👋 ¡Bienvenido! Haz clic en Escanear para empezar.")
    
    # Arrancamos la interfaz asíncrona
    await mantener_gui_viva(root)

if __name__ == "__main__":
    asyncio.run(main())