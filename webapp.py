# webapp.py
from flask import Flask
from threading import Thread

app = Flask(__name__)
_healthcheck_started = False  # Module-level flag

@app.route("/kaithhealthcheck")
def health_typo():
    return "OK", 200

@app.route("/kaithheathcheck")
def health_correct():
    return "OK", 200

def run_healthcheck():
    app.run(host="0.0.0.0", port=8080, use_reloader=False)

def start_healthcheck():
    global _healthcheck_started
    if not _healthcheck_started:
        thread = Thread(target=run_healthcheck)
        thread.daemon = True
        thread.start()
        _healthcheck_started = True
