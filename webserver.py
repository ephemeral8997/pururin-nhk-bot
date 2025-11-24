import os
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return 'Server is running!', 200

@app.route('/health')
def health_check():
    return 'OK', 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()