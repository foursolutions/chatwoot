import os
from flask import Flask, request, jsonify
import dispatcher

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "test")

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    When you set up your Webhook URL in the Meta Business Manager,
    Meta will send a GET request with hub.mode, hub.verify_token, and hub.challenge.
    If the verify_token matches, respond with hub.challenge.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    All incoming WhatsApp messages/events from 360dialog/Meta arrive here as POST.
    We parse the JSON and hand off to dispatcher.handle_event().
    """
    try:
        data = request.get_json()
        # Pass the entire JSON payload to the dispatcher
        dispatcher.handle_event(data)
    except Exception as e:
        # For debugging: log any exceptions
        print("Error in receive_message:", e)

    # Always return 200 to acknowledge receipt (Meta requires this)
    return "OK", 200

if __name__ == "__main__":
    # The app will run on port 5000 by default; Heroku overrides via PROCFILE
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

