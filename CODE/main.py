from flask import Flask, render_template, Response
import time
import json
from datetime import time as dtime
import datetime 
import numpy as np
import schedule
import statistics #for average, median, mode
START_TIME= dtime(8, 0)
END_TIME= dtime(22, 00)

def check_route_time():
    now=datetime.datetime.now().time()
    return START_TIME<=now<=END_TIME

#-------------Merged the two programs here --------------
import serial
import threading
import csv

#-------------INITIALISATION OF ARDUINO------------------
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600

#-------------INITIALISATION of live values--------------

latest_value = 0.0
latest_prediction=0.0
daily_total_volume=0.0

#------------CONFIGURE THE THREADING---------------------
data_lock = threading.Lock() 
prediction_lock = threading.Lock()

#------------READ ARDUINO--------------------------------
def read_arduino_data():
    global latest_value, daily_total_volume
    print(f"Attempting to connect to {SERIAL_PORT} at {BAUD_RATE} baud rate")
    ser = None

    # Track last write to CSV to avoid multiple writes in the same minute
    last_csv_write_date = None

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) 
        print("Connection established. Reading the data, ...")
        print("-" * 30)

        last_update_time = time.time()  # Track time between readings for volume calculation

        while True:
            # ---- READ ARDUINO ----
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        new_value = float(line)  
                        now = time.time()
                        dt_min = (now - last_update_time) / 60.0  
                        last_update_time = now

                        
                        with data_lock:
                            latest_value = new_value+1
                            daily_total_volume += (new_value+1)* dt_min  

                        print(f"Raw data: {line}, Latest value: {latest_value}, Total volume: {daily_total_volume:.2f}")

                    except ValueError:
                        print(f"Received garbage data: {line}")

            
            current_time = datetime.datetime.now()
            
            if current_time.hour == 21 and current_time.minute == 40:
                today_str = current_time.strftime("%Y-%m-%d")
                if last_csv_write_date != today_str:  # Prevent multiple writes in the same minute
                    with data_lock:
                        total_volume_today = daily_total_volume
                    # Append total daily volume to CSV
                    with open("flow_data.csv", 'a', newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([total_volume_today])
                    print(f"Appended daily total volume to CSV: {total_volume_today:.2f} liters for {today_str}")
                    last_csv_write_date = today_str  # mark that CSV write is done for today

            time.sleep(0.1)  

    except serial.SerialException as e:
        print(e)

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

    finally:
        if ser is not None and ser.is_open:
            ser.close()
            print("Serial port closed.")

#----------------NEURAL NETWORK LOGIC----------------------

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_deriv(x):
    s = sigmoid(x)
    return s * (1 - s)

def mse_loss(y_true, y_pred):
    return np.mean((y_true - y_pred) ** 2)

def prepare_training_data_4_input(flows):
    X, y = [], []
    if len(flows) < 5:
        raise ValueError("Flow data must contain at least 5 values.")
    for i in range(len(flows) - 4):
        X.append([flows[i], flows[i+1], flows[i+2], flows[i+3]])
        y.append([flows[i+4]])
    return np.array(X, float), np.array(y, float)

class NeuralNetwork:
    def __init__(self):
        self.X_mean = None
        self.X_std = None
        self.y_mean = None
        self.y_std = None
        self.loss_history = []
        self.W1 = np.random.normal(0,1,(4,16))
        self.b1 = np.random.normal(0,1,(16,))
        self.W2 = np.random.normal(0,1,(16,8))
        self.b2 = np.random.normal(0,1,(8,))
        self.W3 = np.random.normal(0,1,(8,1))
        self.b3 = np.random.normal(0,1,(1,))
        
    def fit_scaler(self,X,y):
        self.X_mean = X.mean(axis=0)
        X_std_raw = X.std(axis=0)
        self.y_mean = y.mean()
        y_std_raw = y.std()
        self.X_std = np.where(X_std_raw==0,1.0,X_std_raw)
        self.y_std = 1.0 if y_std_raw==0 else y_std_raw
        X_norm = (X - self.X_mean)/self.X_std
        y_norm = (y - self.y_mean)/self.y_std
        return X_norm, y_norm
    
    def feedforward(self,X):
        self.z1 = X @ self.W1 + self.b1
        self.h1 = sigmoid(self.z1)
        self.z2 = self.h1 @ self.W2 + self.b2
        self.h2 = sigmoid(self.z2)
        self.z3 = self.h2 @ self.W3 + self.b3
        self.output = sigmoid(self.z3)
        return self.output
    
    def train(self,X,y,lr=0.05,epochs=4000):
        X_norm, y_norm = self.fit_scaler(X,y)
        for epoch in range(epochs):
            out = self.feedforward(X_norm)
            d_out = 2*(out - y_norm) * sigmoid_deriv(self.z3)
            d_W3 = self.h2.T @ d_out
            d_b3 = np.sum(d_out,axis=0)
            d_h2 = d_out @ self.W3.T
            d_z2 = d_h2 * sigmoid_deriv(self.z2)
            d_W2 = self.h1.T @ d_z2
            d_b2 = np.sum(d_z2,axis=0)
            d_h1 = d_z2 @ self.W2.T
            d_z1 = d_h1 * sigmoid_deriv(self.z1)
            d_W1 = X_norm.T @ d_z1
            d_b1 = np.sum(d_z1,axis=0)
            self.W3 -= lr*d_W3
            self.b3 -= lr*d_b3
            self.W2 -= lr*d_W2
            self.b2 -= lr*d_b2
            self.W1 -= lr*d_W1
            self.b1 -= lr*d_b1
    
    def predict_denormalized(self,sample):
        if self.X_mean is None:
            raise ValueError("Model must be trained before prediction.")
        sample_norm = (sample - self.X_mean)/self.X_std
        pred_norm = self.feedforward(sample_norm)
        return pred_norm*self.y_std + self.y_mean

def run_deep_flow_prediction(file_name='flow_data.csv'):
    flows = []
    try:
        with open(file_name,'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    flows.append(float(row[0].strip()))
        flows = np.array(flows,float)
        X, y = prepare_training_data_4_input(flows)
        nn = NeuralNetwork()
        nn.train(X,y,epochs=4000)
        last_four = np.array([[flows[-4],flows[-3],flows[-2],flows[-1]]])
        pred = nn.predict_denormalized(last_four)
        return pred[0][0]
    except Exception as e:
        print("Prediction error:", e)
        return None
    
#----------------DAILY PREDICTION---------------------------

def run_daily_prediction():
    global latest_prediction
    predicted_value = run_deep_flow_prediction('flow_data.csv')
    if predicted_value is not None:
        with prediction_lock:
            latest_prediction = predicted_value
        # Append to CSV for daily record
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        with open('daily_predictions.csv','a',newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date_str, predicted_value])
        print(f"[{datetime.datetime.now()}] Daily prediction updated: {predicted_value:.2f}")

def schedule_prediction():
    schedule.every().day.at("21:45").do(run_daily_prediction)
    while True:
        schedule.run_pending()
        time.sleep(30)


#----------------CREATE FLASK APP WITH SECURE STRING--------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_secure_and_random_string' 

#----------------HOME route---------------------------------
@app.route("/")
def home_page():
    return render_template("mainpage_2.html")

#----------------LIVE route---------------------------------
@app.route("/live")
def live_page():
    return render_template("live report page.html")

#----------------DATA SUPPLY FOR LIVE route-----------------
def generate_data():
    while True:
        with data_lock:
            current_value = latest_value
        data = {
            'value': current_value, 
            'timestamp': time.time()
        }
        print(f"Sending data from Flask:{data}")
        yield f"data: {json.dumps(data)}\n\n"
        time.sleep(0.4)

#---------------STREAM route--------------------------------
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

#---------------DAILY ANALYSIS-------------------------------
@app.route("/analysis")
def analysis_page():
    if not check_route_time():
        return render_template("Unavailable.html") 
    return render_template("daily analysis page.html", prediction=latest_prediction, total_volume=daily_total_volume)

#---------------OVERALL REPORT PAGE--------------------------
@app.route("/overall-report")
def overall_report():
    flow_data_list=[]
    with open("flow_data.csv", 'r', newline="") as f:
        reader=csv.reader(f, delimiter=",")
        for row in reader:
            float_data=float(row[0])
            flow_data_list.append(float_data)
    average=sum(flow_data_list)/len(flow_data_list)
    mode=statistics.mode(flow_data_list)
    median=statistics.median(flow_data_list)
    return render_template("overall-report.html", flow_data=flow_data_list, average=average, mode=mode, median=median)

#---------------RUN THE APP----------------------------------
if __name__ == "__main__":
    thread = threading.Thread(target=read_arduino_data, daemon=True)
    thread.start()
    threading.Thread(target=schedule_prediction, daemon=True).start()
    print("Threader started!!")
    print("Starting the server...")
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False) 
    
