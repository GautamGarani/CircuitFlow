import serial
import time
import threading

SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600
latest_value=0.0

def read_arduino_data():
    global latest_value
    print(f"Attempting to connect to {SERIAL_PORT} at {BAUD_RATE} baud rate")
    ser=None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) 
        print("Connection established. Reading the data, ...")
        print("-" * 30)

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        data_values=line.split(":")[1]
                        latest_value=float(data_values)
                        print(f"Received Sensor Data, and converted to <float>: **{latest_value}**")
                    except ValueError:
                        print(f"Received some data: {line}")
            
            time.sleep(0.05) 

    except serial.SerialException as e:
        print(f"Error details: {e}")
    
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    
    finally:
        if ser.is_open:
            ser.close()
            print("Serial port closed.")

def start_thread():
    thread=threading.Thread(target=read_arduino_data, daemon=True)
    thread.start()
