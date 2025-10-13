# webapp.py
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/kaithhealthcheck")
def health_typo():
    return "OK", 200

@app.route("/kaithheathcheck")
def health_correct():
    return "OK", 200

def run_healthcheck():
    app.run(host="0.0.0.0", port=8080, use_reloader=False)

def start_healthcheck():
    thread = Thread(target=run_healthcheck)
    thread.daemon = True
    thread.start()

start_healthcheck()