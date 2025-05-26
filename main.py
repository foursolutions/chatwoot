# main.py
from flask import Flask, request
from dispatcher import dispatch_message

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    return dispatch_message(request)

@app.route("/", methods=["GET"])
def home():
    return "Chatbot running!", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)