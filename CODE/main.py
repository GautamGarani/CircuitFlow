from flask import Flask, render_template, Response
from reader import start_thread, latest_value
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_secure_and_random_string' 

@app.route("/")
def home_page():
    return render_template("mainpage.html")

@app.route("/live")
def live_page():
    return render_template("live report page.html")

@app.route("/stream")
def stream():
    def generate():
        while True: 
            yield f"data: {latest_value}\n\n"
            time.sleep(0.1)
    return Response(generate(), mimetype="text/event-stream")

@app.route("/analysis")
def analysis_page():
    return render_template("daily analysis page.html")

if __name__ == "__main__":
    start_thread()
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)