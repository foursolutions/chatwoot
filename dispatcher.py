# dispatcher.py
import os
import json
from flask import Flask, request, Response
from helpers import (
    send_text_message,
    send_interactive_message,
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

# Webhook verification (GET)
@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification token mismatch", 403

# Main webhook endpoint (POST)
@app.route("/webhook", methods=["POST"])
def receive_message():
    payload = request.get_json(force=True)
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # This structure partial depends on 1msg’s “cloud webhook” format:
    #   { "entry": [ { "changes": [ { "value": { "messages": […] } } ] } ] }
    entry   = payload.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value   = changes.get("value", {})
    messages = value.get("messages", [])
    if not messages:
        return Response(status=200)

    message = messages[0]
    raw_from = message.get("from", "")
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from
    msg_type = message.get("type", "")
    text_body = ""
    if msg_type == "text":
        text_body = message["text"]["body"].strip().lower()

    # If the user sends “reset”, clear all states and send main menu
    if msg_type == "text" and text_body == "reset":
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

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

    # If user replies by tapping a button:
    if msg_type == "button":
        button_id = message["button"]["payload"]
        if button_id == "help_pest":
            set_user_state("car", from_number, {})
            return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)
        if button_id == "help_mold":
            set_user_state("mold", from_number, {})
            return handle_mold_flow(from_number, message, API_KEY, BASE_URL)
        if button_id == "live_human":
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "Sure—one of our agents will be with you shortly." }
            })
            return Response(status=200)

    # If user sends free-text and is already in a flow, delegate appropriately:
    user_state_car = get_user_state("car", from_number)
    if user_state_car:
        return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

    user_state_bedbug = get_user_state("bedbug", from_number)
    if user_state_bedbug:
        return handle_bedbug_flow(from_number, message, API_KEY, BASE_URL)

    user_state_mold = get_user_state("mold", from_number)
    if user_state_mold:
        return handle_mold_flow(from_number, message, API_KEY, BASE_URL)

    # Otherwise, if this is just raw “Hello” or any other text, show main menu:
    if msg_type == "text":
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

    return Response(status=200)
# end dispatcher.py
