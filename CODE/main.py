from flask import Flask, render_template, Response
import time
import json
import reader

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
        reader.new_data_event.wait()        #wait for new data
        reader.new_data_event.clear()      

        with reader.data_lock:
            current_value = reader.latest_value

        data = {
            "value": current_value,
            "timestamp": time.time()
        }

        print(f"Flask sending: {data}")
        yield f"data: {json.dumps(data)}\n\n"

@app.route("/analysis")
def analysis_page():
    return render_template("daily analysis page.html")

@app.route("/stream")
def stream():
    return Response(
        generate_data(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
