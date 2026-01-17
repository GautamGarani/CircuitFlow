from flask import Flask, render_template, Response
import time
import json
from datetime import time as dtime
import datetime
import numpy as np
import schedule
import statistics
import serial
import threading
import csv
from datetime import date

START_TIME = dtime(8, 0)
END_TIME = dtime(10, 0)

def check_route_time():
    now = datetime.datetime.now().time()
    return (now >= END_TIME) or (now <= START_TIME)

# ------------- INITIALISATION OF ARDUINO ------------------
SERIAL_PORT = 'COM4'
BAUD_RATE = 9600

# ------------- INITIALISATION of live values --------------
latest_value = 0.0
latest_prediction = 0.0
daily_total_volume = 0.0

# ------------ CONFIGURE THE THREADING ---------------------
data_lock = threading.Lock()
prediction_lock = threading.Lock()

# ------------ READ ARDUINO --------------------------------
def read_arduino_data():
    global latest_value, daily_total_volume
    ser = None
    last_csv_write_date = None

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        last_update_time = time.time()

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        new_value = float(line)
                        now = time.time()
                        dt_min = (now - last_update_time) / 60.0
                        last_update_time = now

                        with data_lock:
                            latest_value = new_value
                            daily_total_volume += new_value * dt_min

                    except ValueError:
                        pass

            current_time = datetime.datetime.now()
            if current_time.hour == 18 and current_time.minute == 19:
                today_str = current_time.strftime("%Y-%m-%d")
                if last_csv_write_date != today_str:
                    with data_lock:
                        total_volume_today = daily_total_volume

                    with open("flow_data_old.csv", "a", newline="") as f:
                        writer = csv.DictWriter(
                            f, fieldnames=["Date", "Flow"]
                        )
                        if f.tell() == 0:
                            writer.writeheader()
                        writer.writerow({
                            "Date": today_str,
                            "Flow": total_volume_today
                        })

                    last_csv_write_date = today_str

            time.sleep(0.1)

    finally:
        if ser and ser.is_open:
            ser.close()

# ---------------- NEURAL NETWORK LOGIC ---------------------
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_deriv(x):
    s = sigmoid(x)
    return s * (1 - s)

def prepare_training_data_4_input(flows):
    X, y = [], []
    for i in range(len(flows) - 4):
        X.append([flows[i], flows[i+1], flows[i+2], flows[i+3]])
        y.append([flows[i+4]])
    return np.array(X, float), np.array(y, float)

class NeuralNetwork:
    def __init__(self):
        self.W1 = np.random.normal(0,1,(4,16))
        self.b1 = np.random.normal(0,1,(16,))
        self.W2 = np.random.normal(0,1,(16,8))
        self.b2 = np.random.normal(0,1,(8,))
        self.W3 = np.random.normal(0,1,(8,1))
        self.b3 = np.random.normal(0,1,(1,))

    def fit_scaler(self, X, y):
        self.X_mean = X.mean(axis=0)
        self.X_std = np.where(X.std(axis=0)==0,1,X.std(axis=0))
        self.y_mean = y.mean()
        self.y_std = y.std() if y.std()!=0 else 1
        return (X-self.X_mean)/self.X_std, (y-self.y_mean)/self.y_std

    def feedforward(self, X):
        self.z1 = X @ self.W1 + self.b1
        self.h1 = sigmoid(self.z1)
        self.z2 = self.h1 @ self.W2 + self.b2
        self.h2 = sigmoid(self.z2)
        self.z3 = self.h2 @ self.W3 + self.b3
        return sigmoid(self.z3)

    def train(self, X, y, lr=0.05, epochs=4000):
        Xn, yn = self.fit_scaler(X, y)
        for _ in range(epochs):
            out = self.feedforward(Xn)
            d = 2*(out-yn) * sigmoid_deriv(self.z3)
            self.W3 -= lr * self.h2.T @ d
            self.b3 -= lr * d.sum(axis=0)

    def predict_denormalized(self, sample):
        sn = (sample - self.X_mean)/self.X_std
        pred = self.feedforward(sn)
        return pred*self.y_std + self.y_mean

def run_deep_flow_prediction(file_name="flow_data_old.csv"):
    flows = []
    with open(file_name, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            flows.append(float(row["Flow"]))

    flows = np.array(flows, float)

   
    X, y = prepare_training_data_4_input(flows)

    #TIME SERIES SPLIT
    n = len(X)
    train_end = int(0.7 * n)
    val_end = int(0.85 * n)

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    
    nn = NeuralNetwork()
    nn.train(X_train, y_train)

    # Predict next day
    last_four = np.array([[flows[-4], flows[-3], flows[-2], flows[-1]]], float)
    return nn.predict_denormalized(last_four)[0][0]

# ---------------- DAILY PREDICTION ------------------------
def run_daily_prediction():
    global latest_prediction
    predicted_value = run_deep_flow_prediction("flow_data.csv")
    with prediction_lock:
        latest_prediction = predicted_value

    date_str = date.today().strftime("%Y-%m-%d")
    with open("daily_predictions.csv", "a", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["Date", "Predicted Values"]
        )
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow({
            "Date": date_str,
            "Predicted Values": predicted_value
        })

def schedule_prediction():
    schedule.every().day.at("15:25").do(run_daily_prediction)
    while True:
        schedule.run_pending()
        time.sleep(30)

# ---------------- FLASK APP -------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'myrandomstring'

@app.route("/")
def home_page():
    return render_template("mainpage_2.html")

@app.route("/live")
def live_page():
    return render_template("live report page.html")

def generate_data():
    while True:
        with data_lock:
            val = latest_value
        yield f"data: {json.dumps({'value': val})}\n\n"
        time.sleep(0.4)

@app.route("/stream")
def stream():
    return Response(generate_data(), mimetype='text/event-stream')

@app.route("/analysis")
def analysis_page():
    return render_template(
        "daily analysis page.html",
        prediction=latest_prediction,
        total_volume=daily_total_volume
    )

@app.route("/overall-report")
def overall_report():
    flow_data_list = []
    with open("flow_data.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            flow_data_list.append(float(row["Flow"]))

    average = sum(flow_data_list)/len(flow_data_list)
    mode = statistics.mode(flow_data_list)
    median = statistics.median(flow_data_list)

    if not check_route_time():
        return render_template("Unavailable.html")

    return render_template(
        "overall-report.html",
        flow_data=flow_data_list,
        average=average,
        mode=mode,
        median=median
    )

# ---------------- RUN APP ---------------------------------
if __name__ == "__main__":
    threading.Thread(target=read_arduino_data, daemon=True).start()
    threading.Thread(target=schedule_prediction, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
