# main.py
import os
from flask import Flask, request

from dispatcher import dispatch_message

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return "Chatbot running!"

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    # Only process POSTs from Twilio
    if request.method == "POST":
        dispatch_message(request)
        return "OK", 200
    return "Webhook endpoint ready", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
