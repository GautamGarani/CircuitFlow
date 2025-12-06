import serial
import time

SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600
# ---------------------

def read_arduino_data():
    
    print(f"Attempting to connect to {SERIAL_PORT} at {BAUD_RATE} baud...")
    
    try:
        
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) 
        print("Connection established. Reading data...")
        print("-" * 30)

        
        while True:
            
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                
                if line:
                    try:
                        
                        data_value = int(line)
                        print(f"Received Sensor Data: **{data_value}**")
                    except ValueError:
                       
                        print(f"Received some data: {line}")
            
            time.sleep(0.05) 

    except serial.SerialException as e:
        print(f"\n--- ERROR ---")
        print(f"Could not open serial port {SERIAL_PORT}. Please check:")
        print(f"* Is the Arduino connected?")
        print(f"* Is the port name correct? (e.g., 'COM3' or '/dev/ttyUSB0')")
        print(f"* Is the Arduino IDE's Serial Monitor closed?")
        print(f"Error details: {e}")
    
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    
    finally:
        
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    read_arduino_data()