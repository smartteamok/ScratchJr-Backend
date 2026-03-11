let secuencia: number[] = []
let ultimaVez = 0

basic.showIcon(IconNames.Asleep)

bluetooth.onBluetoothConnected(function () {
    basic.clearScreen()
})

bluetooth.onBluetoothDisconnected(function () {
    basic.showIcon(IconNames.Asleep)
})

bluetooth.onUartDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    let datos = bluetooth.uartReadBuffer()
    for (let i = 0; i < datos.length; i++) {
        let dato = datos[i]

        // --- 1. MODO EJECUCIÓN (START) ---
        if (dato == 0xF0) {
            for (let opcode of secuencia) {
                if (opcode == 6) {
                    // Si toca el mensaje, lo enviamos a la Mac
                    let respuesta = pins.createBuffer(1)
                    respuesta.setNumber(NumberFormat.UInt8LE, 0, 0xAA)
                    bluetooth.uartWriteBuffer(respuesta)

                    // Mostramos un puntito rápido y mantenemos el ritmo de la secuencia
                    led.plot(2, 2)
                    basic.pause(100)
                    led.unplot(2, 2)
                    basic.pause(500)
                }
                else {
                    // Si es un ícono normal
                    if (opcode == 1) basic.showIcon(IconNames.Heart)
                    else if (opcode == 2) basic.showIcon(IconNames.Square)
                    else if (opcode == 3) basic.showIcon(IconNames.Triangle)
                    else if (opcode == 4) basic.showIcon(IconNames.Yes)
                    else if (opcode == 5) basic.showIcon(IconNames.No)

                    basic.pause(600)
                    basic.clearScreen()
                }
                basic.pause(200) // Pausa entre pasos
            }
        }
        // --- 2. MODO CONFIGURACIÓN (Guardar en memoria del 1 al 6) ---
        else if (dato >= 1 && dato <= 6) {
            if (control.millis() - ultimaVez > 1500) {
                secuencia = []
            }
            secuencia.push(dato)
            ultimaVez = control.millis()

            // Feedback de guardado
            led.plot(2, 2)
            basic.pause(100)
            led.unplot(2, 2)
        }
    }
})

bluetooth.startUartService()
