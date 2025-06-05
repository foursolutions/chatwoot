# begin dispatcher.py
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

VERIFY_TOKEN     = os.environ.get("VERIFY_TOKEN", "")
API_KEY          = os.environ.get("1MSG_API_KEY", "")
BASE_URL         = os.environ.get("1MSG_BASE_URL", "")     # e.g. https://api.1msg.io/VAN123456
NAMESPACE        = os.environ.get("1MSG_NAMESPACE", "")     # e.g. 94d66366_9ec1_43a3_a84c_46039bd33ef5
LANG_CODE        = os.environ.get("1MSG_LANG_CODE", "en")   # e.g. "en"
MAIN_MENU_TEMPLATE = os.environ.get("MAIN_MENU_TEMPLATE", "main_menu_v2")

# Webhook verification (GET)
@app.route("/webhook", methods=["GET"])
def verify():
    # Facebook/WhatsApp/1msg verification handshake
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification token mismatch", 403

# Main webhook endpoint (POST)
@app.route("/webhook", methods=["POST"])
def receive_message():
    raw = request.get_data(as_text=True)

    # If 1msg sometimes sends a raw string instead of JSON object, try to parse:
    try:
        payload = json.loads(raw)
    except:
        payload = request.get_json(force=True)

    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # ── STEP 0 ── Ignore any "ack" payload. If there's an "ack" field, 1msg is simply reporting
    #              that a template/text we sent earlier was delivered. We don't want to reply again.
    if "ack" in payload:
        return Response(status=200)

    # ── STEP 1 ── If there's no "messages" array (empty or missing), nothing to do.
    if "messages" not in payload or not isinstance(payload["messages"], list):
        return Response(status=200)

    entry = payload["messages"][0]
    msg_type = entry.get("type", "")

    # ── STEP 2 ── Extract phone number ("from"). 1msg will send "author" or "chatId" in most webhooks.
    raw_from = entry.get("from", "") or entry.get("author", "")
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from

    # ── STEP 3 ── Grasp the textual body if this is a chat/text
    text_body = ""
    if msg_type == "chat":
        text_body = entry.get("body", "").strip().lower()

    # ── STEP 4 ── If user literally typed "reset", clear states & send main menu template
    if msg_type == "chat" and text_body == "reset":
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send the template menu (main_menu_v2) via send_template_message:
        send_template_message(
            to=from_number,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=["there"]
        )
        return Response(status=200)

    # ── STEP 5 ── If user tapped a quick‐reply button, 1msg will send type="interactive"
    if msg_type == "interactive":
        interactive = entry.get("interactive", {})
        # There are two kinds: button_reply or list_reply; here we only care about button_reply
        button_reply = interactive.get("button_reply", None)
        if button_reply:
            button_id = button_reply.get("id", "")
            if button_id == "help_pest":
                set_user_state("car", from_number, {})
                return handle_car_fumigation_flow(from_number, entry, API_KEY, BASE_URL)
            if button_id == "help_mold":
                set_user_state("mold", from_number, {})
                return handle_mold_flow(from_number, entry, API_KEY, BASE_URL)
            if button_id == "live_human":
                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "text": {"body": "Sure—one of our agents will be with you shortly."},
                    "messaging_product": "whatsapp"
                })
                return Response(status=200)

    # ── STEP 6 ── If user is already in a car flow and they sent free text (type=chat),
    #              delegate to car_fumigation.
    user_state_car = get_user_state("car", from_number)
    if user_state_car:
        return handle_car_fumigation_flow(from_number, entry, API_KEY, BASE_URL)

    user_state_bedbug = get_user_state("bedbug", from_number)
    if user_state_bedbug:
        return handle_bedbug_flow(from_number, entry, API_KEY, BASE_URL)

    user_state_mold = get_user_state("mold", from_number)
    if user_state_mold:
        return handle_mold_flow(from_number, entry, API_KEY, BASE_URL)

    # ── STEP 7 ── Otherwise, if this is a plain chat/text (not in a flow), send the main_menu_v2
    if msg_type == "chat":
        send_template_message(
            to=from_number,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=["there"]
        )
        return Response(status=200)

    return Response(status=200)
# end dispatcher.py
