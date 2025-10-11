# healthcheck.py
from flask import Flask

app = Flask(__name__)


@app.route("/kaithheathcheck")
def health():
    return "OK", 200


app.run(host="0.0.0.0", port=8080)
