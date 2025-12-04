<p align="center"><img src="../Images/circuitflow_logo.png" alt="CircuitFlow Logo" width="100" height="100">
</p>

# Pyserial:
Pyserial is python's standard library for communicating with serial ports.

## Installation:
```bash
pip install pyserial
```
## The Core: serial.Serial

```bash
import serial
ser=serial.Serial(port='COM3', baudrate=9600, timeout=1)
```

What the parameters mean:<br>
(a) Port: The serial port name
<br>
(b) Baudrate: The speed at which data is read from Arduino
<br>
(c) Timeout: Seconds to wait for data before giving up.

## Important Methods:
### ser.readline()
Reads until a newline. This works well with Arduino's ``Serial.println()``
## in_waiting:
It specifies the number of bytes waiting to be read
<br>
example:

```bash
if serial.in_waiting>0:
    data=ser.readline()
```

## Loop for live data:
```bash
import serial
import time

ser=serial.Serial('COM3', 9600, timeout=1)
time.sleep(2) #waits for Arduino to reset

while True:
    if ser.in_waiting:
        line=ser.readline().decode().strip()
        print(line)

```
## Exceptions:
```bash
try:
    ser.readline()
except serial.SerialException:
    print("Serial Disconnected")
```
Date: 04/12/2025