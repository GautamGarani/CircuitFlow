import serial
import time
import threading
import csv

SERIAL_PORT = 'COM4' 
BAUD_RATE = 9600
latest_value=0.0

data_lock=threading.Lock()

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
                        #data_values=line.split(":")[0]
                        new_value=float(line)
                        with data_lock:
                            latest_value=new_value
                        print(f"Received Sensor Data, and converted to <float>: {latest_value}")
                        with open("flow_data.csv", 'a', newline="") as f:
                            filewriter=csv.writer(f)
                            filewriter.writerow([latest_value])
                    except ValueError:
                        print(f"Received some data: {line}")
                    

    except serial.SerialException as e:
        print(f"Error details: {e}")
    
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    
    finally:
        if ser is not None:
            if ser.is_open:
                ser.close()
                print("Serial port closed.")

try: 
    thread=threading.Thread(target=read_arduino_data, daemon=True).start()
    print("Threader started successfully")
except:
    print("threading failed to start")

