# begin dispatcher.py
import os
import json
from flask import Flask, request, Response
from helpers import (
    send_text_message,
    send_interactive_message,
    send_template_message,  # ← newly added
    get_user_state,
    set_user_state,
    clear_user_state
)
from flows.car_fumigation import handle_car_fumigation_flow
from flows.bedbug import handle_bedbug_flow
from flows.mold import handle_mold_flow

app = Flask(__name__)

VERIFY_TOKEN    = os.environ.get("VERIFY_TOKEN", "")
API_KEY         = os.environ.get("1MSG_API_KEY", "")
BASE_URL        = os.environ.get("1MSG_BASE_URL", "")      # e.g. https://api.1msg.io/VAN123456
NAMESPACE       = os.environ.get("1MSG_NAMESPACE", "")     # e.g. 94d66366_9ec1_43a3_a84c_46039bd33ef5
LANG_CODE       = os.environ.get("1MSG_LANG_CODE", "en")   # default "en"
MAIN_MENU_NAME  = os.environ.get("MAIN_MENU_TEMPLATE", "main_menu_v2")

# -------------------------------------------------------------------
# Webhook verification (GET)
# -------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify():
    # Facebook/WhatsApp/1msg verification handshake
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification token mismatch", 403

# -------------------------------------------------------------------
# Main webhook endpoint (POST)
# -------------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def receive_message():
    payload = request.get_json(force=True)
    # Log for debugging
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # Extract the "from" phone number and message type
    entry   = payload.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value   = changes.get("value", {})
    messages = value.get("messages", [])
    if not messages:
        return Response(status=200)

    message    = messages[0]
    raw_from   = message.get("from", "")
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from
    msg_type   = message.get("type", "")
    text_body  = ""
    if msg_type == "text":
        text_body = message["text"]["body"].strip().lower()

    # ----------------------------------------------------------------
    # 1) User typed "reset" → clear all states & send main menu TEMPLATE
    # ----------------------------------------------------------------
    if msg_type == "text" and text_body == "reset":
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send the 1msg-approved "main_menu_v2" template (no manual JSON)
        # We pass a single body placeholder "there" to fill {{1}} in your template
        send_template_message(
            to=from_number,
            template_name=MAIN_MENU_NAME,
            template_params=["there"]
        )
        return Response(status=200)

    # ----------------------------------------------------------------
    # 2) User tapped a template quick-reply button (payload from 1msg)
    # ----------------------------------------------------------------
    if msg_type == "button":
        button_id = message["button"]["payload"]  # e.g. "help_pest", "help_mold", "live_human"
        if button_id == "help_pest":
            set_user_state("car", from_number, {})
            return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

        if button_id == "help_mold":
            set_user_state("mold", from_number, {})
            return handle_mold_flow(from_number, message, API_KEY, BASE_URL)

        if button_id == "live_human":
            # Just send a plain text acknowledgment
            send_text_message({
                "to": from_number,
                "type": "text",
                "text": { "body": "Sure—one of our agents will be with you shortly." },
                "messaging_product": "whatsapp"
            })
            return Response(status=200)

    # ----------------------------------------------------------------
    # 3) If user is mid-flow, delegate to the correct handler
    # ----------------------------------------------------------------
    user_state_car   = get_user_state("car", from_number)
    if user_state_car:
        return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

    user_state_bedbug = get_user_state("bedbug", from_number)
    if user_state_bedbug:
        return handle_bedbug_flow(from_number, message, API_KEY, BASE_URL)

    user_state_mold  = get_user_state("mold", from_number)
    if user_state_mold:
        return handle_mold_flow(from_number, message, API_KEY, BASE_URL)

    # ----------------------------------------------------------------
    # 4) Fallback: raw text ("hello", etc.) → send main menu TEMPLATE
    # ----------------------------------------------------------------
    if msg_type == "text":
        send_template_message(
            to=from_number,
            template_name=MAIN_MENU_NAME,
            template_params=["there"]
        )
        return Response(status=200)

    return Response(status=200)
# end dispatcher.py

