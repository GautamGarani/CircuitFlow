from flask import Flask, render_template, request
app = Flask(__name__)

@app.route("/")
def home_page():
    return render_template("mainpage.html")

@app.route("/live")
def live_page():
    return render_template("live report page.html")

@app.route("/analysis")
def analysis_page():
    return render_template("daily analysis page.html")

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8000) 