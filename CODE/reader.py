import serial
import time

# --- Configuration ---
# 1. Change 'COM3' to the actual serial port your Arduino is connected to
#    (e.g., 'COM3' on Windows, '/dev/ttyACM0' or '/dev/ttyUSB0' on Linux, or '/dev/cu.usbmodemXXXX' on macOS)
# 2. Baud rate MUST match the Serial.begin(9600) in the Arduino code
SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600
# ---------------------

def read_arduino_data():
    """Connects to the Arduino and continuously prints the sensor data."""
    print(f"Attempting to connect to {SERIAL_PORT} at {BAUD_RATE} baud...")
    
    try:
        # Open the serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Give the port time to initialize
        print("Connection established. Reading data...")
        print("-" * 30)

        # Loop forever, reading and printing data
        while True:
            # Read a line of data sent by the Arduino
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                # Check if the line is not empty and contains a number
                if line:
                    try:
                        # Convert the received string data to an integer (optional, but useful)
                        data_value = int(line)
                        print(f"Received Sensor Data: **{data_value}**")
                    except ValueError:
                        # Handle cases where the received line isn't a clean number
                        print(f"Received some data: {line}")
            
            time.sleep(0.05) # Small delay to prevent constant CPU usage

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
        # Close the serial port when the program exits
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    read_arduino_data()