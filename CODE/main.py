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
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

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
            if current_time.hour == 10 and current_time.minute == 00:
                today_str = current_time.strftime("%Y-%m-%d")
                if last_csv_write_date != today_str:
                    with data_lock:
                        total_volume_today = daily_total_volume

                    with open("flow_data.csv", "a", newline="") as f:
                        writer = csv.DictWriter(
                            f, fieldnames=["Date", "Flow"]
                        )
                        if f.tell() == 0:
                            writer.writeheader()
                        writer.writerow({
                            "Date": today_str,
                            "Flow": f"{total_volume_today:.4f}"
                        })

                    last_csv_write_date = today_str

            time.sleep(0.1)

    finally:
        if ser and ser.is_open:
            ser.close()

# ---------------- GRADIENT BOOSTING ---------------------

def monsoon_strength(month):
    #Monsoon encoding using IMD data
    if month == 6: return 0.5
    elif month in [7, 8]: return 1.0
    elif month == 9: return 0.7
    else: return 0.0

def prepare_training_data_4_input_seasonal(flows, dates):
    # Logarithmic transformation 
    # np.log1p for handling case where zero comes
    log_flows = np.log1p(flows)
    
    X, y = [], []
    for i in range(len(log_flows) - 4):
        date_obj = dates[i + 4]
        doy = date_obj.timetuple().tm_yday
        month = date_obj.month

        # Cyclical encoding
        sin_doy = np.sin(2 * np.pi * doy / 365)
        cos_doy = np.cos(2 * np.pi * doy / 365)
        monsoon = monsoon_strength(month)

        X.append([
            log_flows[i], log_flows[i+1], log_flows[i+2], log_flows[i+3],
            sin_doy, cos_doy, monsoon
        ])
        y.append(log_flows[i+4]) # Target is also in log space
    return np.array(X, float), np.array(y, float)

def run_deep_flow_prediction(file_name="flow_data.csv"):
    flows = []
    dates = []
    
    with open(file_name, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            flows.append(float(row.get(" Flow") or row.get("Flow")))
            dates.append(datetime.datetime.strptime(row["Date"], "%Y-%m-%d").date())

    flows = np.array(flows, float)
    X, y = prepare_training_data_4_input_seasonal(flows, dates)

    n = len(X)
    train_end = int(0.7 * n)
    X_train, y_train = X[:train_end], y[:train_end]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=3,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)

    last_date = dates[-1]
    doy = last_date.timetuple().tm_yday
    
    last_4_flows_log = np.log1p([flows[-4], flows[-3], flows[-2], flows[-1]])
    
    last_input = np.array([[
        last_4_flows_log[0], last_4_flows_log[1], 
        last_4_flows_log[2], last_4_flows_log[3],
        np.sin(2 * np.pi * doy / 365),
        np.cos(2 * np.pi * doy / 365),
        monsoon_strength(last_date.month)
    ]], float)

    last_input_scaled = scaler.transform(last_input)
    
    log_prediction = model.predict(last_input_scaled)[0]
    
    # Inverse transform to bring it back from log
    prediction = np.expm1(log_prediction)
    return prediction

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
    schedule.every().day.at("10:01").do(run_daily_prediction)
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