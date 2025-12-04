from flask import Flask, render_template, request


app = Flask(__name__)

app.secret_key = "a-very-secure-random-string-12345" 

@app.route("/")
def home_page():

    return render_template("ui_2.html")

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8000) 