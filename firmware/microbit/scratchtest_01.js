let secuencia: number[] = []
let ultimaVez = 0

// 1. Al iniciar, mostramos la cara de espera
basic.showIcon(IconNames.Asleep)

// 2. Evento: Cuando el Bluetooth se conecta exitosamente
bluetooth.onBluetoothConnected(function () {
    basic.clearScreen() // Limpiamos la pantalla al conectar
})

// 3. Evento: Si se desconecta, volvemos a mostrar la cara
bluetooth.onBluetoothDisconnected(function () {
    basic.showIcon(IconNames.Asleep)
})

bluetooth.onUartDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    let datos = bluetooth.uartReadBuffer()
    for (let i = 0; i < datos.length; i++) {
        let dato = datos[i]

        if (dato == 0xF0) { // START
            for (let opcode of secuencia) {
                if (opcode == 1) basic.showIcon(IconNames.Heart)
                else if (opcode == 2) basic.showIcon(IconNames.Square)
                else if (opcode == 3) basic.showIcon(IconNames.Triangle)
                else if (opcode == 4) basic.showIcon(IconNames.Yes)
                else if (opcode == 5) basic.showIcon(IconNames.No)
                basic.pause(600)
                basic.clearScreen()
                basic.pause(200)
            }
        }
        else if (dato >= 1 && dato <= 5) {
            if (control.millis() - ultimaVez > 1500) {
                secuencia = []
            }
            secuencia.push(dato)
            ultimaVez = control.millis()

            // Feedback visual: parpadeo del LED central (2,2)
            led.plot(2, 2)
            basic.pause(100)
            led.unplot(2, 2) // <-- Corregido aquí
        }
    }
})

bluetooth.startUartService()
