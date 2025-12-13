from flask import Flask, jsonify, render_template, Response
import time
import json
#Merged the two programs here --------------
import serial
import threading
import csv

SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
latest_value = 0.0
data_lock = threading.Lock() 

def read_arduino_data():
    global latest_value
    print(f"Attempting to connect to {SERIAL_PORT} at {BAUD_RATE} baud rate")
    ser = None
    
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

                        new_value = float(line)
                        calculated_value = new_value + 1.00
                        
                        with data_lock:
                            latest_value = calculated_value
                        
                        print(f"Received Sensor Data: {new_value}, and added one: {latest_value}")
                        
                        with open("flow_data.csv", 'a', newline="") as f:
                            filewriter = csv.writer(f)
                            filewriter.writerow([latest_value]) 
                            
                    except ValueError:
                        print(f"Received garbage data: {line}")
            
           
            time.sleep(0.1) 

    except serial.SerialException as e:
        print(e)
        
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    
    finally:
        if ser is not None and ser.is_open:
            ser.close()
            print("Serial port closed.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_secure_and_random_string' 

@app.route("/")
def home_page():
    return render_template("mainpage.html")

@app.route("/live")
def live_page():
    return render_template("live report page.html")

def generate_data():
    while True:
        with data_lock:
            current_value = latest_value

        data = {
            'value': current_value, 
            'timestamp': time.time()
        }
        
        yield f"data: {json.dumps(data)}\n\n"
        
        time.sleep(0.4)

@app.route("/stream")
def stream():
    return Response(
        generate_data(), 
        mimetype='text/event-stream', 
        headers={
            'Cache-Control': 'no-cache', 
            'X-Accel-Buffering': 'no'
        }
    )

'''@app.route("/analysis")
def analysis_page():
    return render_template("daily analysis page.html")'''


if __name__ == "__main__":
    thread = threading.Thread(target=read_arduino_data, daemon=True)
    thread.start()
    print("Starting the server...")
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False) 
