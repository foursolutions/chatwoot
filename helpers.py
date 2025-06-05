# dispatcher.py

import os
import json
from flask import Flask, request, Response

from helpers import (
    send_text_message,
    send_interactive_message,
    send_template_message,
    get_user_state,
    set_user_state,
    clear_user_state
)
from flows.car_fumigation import handle_car_fumigation_flow
from flows.bedbug import handle_bedbug_flow
from flows.mold import handle_mold_flow

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
API_KEY      = os.environ.get("1MSG_API_KEY", "")
BASE_URL     = os.environ.get("1MSG_BASE_URL", "")  # e.g. https://api.1msg.io/VAN123456

# ----------------------------------------------------------------------------
# Webhook Verification (GET)
# ----------------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify():
    # 1msg / WhatsApp handshake for GET verification
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification token mismatch", 403

# ----------------------------------------------------------------------------
# Main Webhook Endpoint (POST)
# ----------------------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def receive_message():
    payload = request.get_json(force=True)
    # Debug: log the raw incoming JSON
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # Facebook/WhatsApp-style wrapper: “entry” → “changes” → “value” → “messages”
    entry   = payload.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value   = changes.get("value", {})
    messages = value.get("messages", [])

    if not messages:
        # No user‐sent message → ignore
        return Response(status=200)

    message    = messages[0]
    raw_from   = message.get("from", "")
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from
    msg_type   = message.get("type", "")
    text_body  = ""

    if msg_type == "text":
        text_body = message["text"]["body"].strip().lower()

    # --------------------------------------------------------
    # If user types “reset” (plain text), clear all states and send main menu again
    # --------------------------------------------------------
    if msg_type == "text" and text_body == "reset":
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Build the interactive button menu “Main Menu”
        interactive_payload = {
            "to": from_number,
            "type": "interactive",
            "messaging_product": "whatsapp",
            "interactive": {
                "type": "button",
                "body": {
                    "text": (
                        "Hi there, thanks for reaching out to Four Solutions! "
                        "I'm Solvia, your fun and friendly chatbot.\n"
                        "How may I help you today? (Tap \"Live Human\" anytime, "
                        "or choose one of the options below.)"
                    )
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "help_pest",
                                "title": "Need help on Pest!"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "help_mold",
                                "title": "Need help on Mold!"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "live_human",
                                "title": "Live Human"
                            }
                        }
                    ]
                }
            }
        }
        send_interactive_message(interactive_payload)
        return Response(status=200)

    # --------------------------------------------------------
    # If user taps an interactive button (“help_pest”, “help_mold”, “live_human”), msg_type == "button"
    # --------------------------------------------------------
    if msg_type == "button":
        button_payload = message["button"]["payload"]  # e.g. "help_pest" or "help_mold" or "live_human"

        # If user tapped “Need help on Pest!”, route into the Car Fumigation flow
        if button_payload == "help_pest":
            return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

        # If user tapped “Need help on Mold!”, route into the Mold flow
        elif button_payload == "help_mold":
            return handle_mold_flow(from_number, message, API_KEY, BASE_URL)

        # If user tapped “Live Human”, simply send a notice or handoff to agent
        elif button_payload == "live_human":
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {
                    "body": (
                        "Connecting you to a live agent now. Please hold on..."
                    )
                }
            })
            return Response(status=200)

    # --------------------------------------------------------
    # If user selects from an interactive “List” (e.g. pest type, date, etc.), msg_type == "interactive"
    # The payload for lists also uses message["interactive"]["list_reply"]["id"]
    # We dispatch to the appropriate flow based on state.
    # --------------------------------------------------------
    if msg_type == "interactive":
        interactive_obj = message["interactive"]
        # “list_reply” is used for single‐select lists
        if interactive_obj.get("list_reply"):
            list_id = interactive_obj["list_reply"]["id"]

            # We need to know which flow the user is currently in.
            # If car‐fumigation state exists, delegate to Car Fumigation flow
            if get_user_state("car", from_number):
                return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

            # Similarly for bedbug or mold
            if get_user_state("bedbug", from_number):
                return handle_bedbug_flow(from_number, message, API_KEY, BASE_URL)

            if get_user_state("mold", from_number):
                return handle_mold_flow(from_number, message, API_KEY, BASE_URL)

            # If no state, check if this is the first service list selection
            # (e.g. user tapped “Need help on Pest!” → Car Fumigation service list)
            # In other words, we haven’t set any state yet → call handle_car_fumigation_flow
            return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

    # --------------------------------------------------------
    # Fallback: if text doesn’t match “reset” and isn’t an interactive button/list,
    # send a “Please tap a button or type 'reset'” message
    # --------------------------------------------------------
    send_text_message({
        "to": from_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {
            "body": "Sorry, I didn’t understand that. Please tap one of the menu buttons or type \"reset\" to start over."
        }
    })
    return Response(status=200)

# ----------------------------------------------------------------------------
# If you ever want to run dispatcher.py locally:
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
