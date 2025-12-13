import serial
import time
import threading
import csv

SERIAL_PORT = "COM4"
BAUD_RATE = 9600

latest_value = 0.0
data_lock = threading.Lock()

# >>> CHANGED: Event to signal new data arrival
new_data_event = threading.Event()

def read_arduino_data():
    global latest_value
    ser = None

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("Reading the data, CONNECTED")

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").strip()
                try:
                    new_value = float(line)

                    with data_lock:
                        latest_value = new_value
                    print(f"Received sensor data and converted to float:{latest_value}")
                    #CHANGED: Notify Flask about the new data immediately
                    new_data_event.set()

                    print(f"Sensor value: {latest_value}")

                    with open("flow_data.csv", "a", newline="") as f:
                        csv.writer(f).writerow([time.time(), latest_value])

                except ValueError:
                    print(f"Ignored invalid data: {line}")

    except serial.SerialException as e:
        print(f"Serial error: {e}")

    finally:
        if ser and ser.is_open:
            ser.close()


thread = threading.Thread(target=read_arduino_data, daemon=True)
thread.start()
print("thread started")
