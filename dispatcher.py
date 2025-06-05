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

VERIFY_TOKEN       = os.environ.get("VERIFY_TOKEN", "")
API_KEY            = os.environ.get("1MSG_API_KEY", "")
BASE_URL           = os.environ.get("1MSG_BASE_URL", "")       # e.g. https://api.1msg.io/VAN123456
NAMESPACE          = os.environ.get("1MSG_NAMESPACE", "")      # e.g. 94d66366_9ec1_43a3_a84c_46039bd33ef5
LANG_CODE          = os.environ.get("1MSG_LANG_CODE", "en")    # e.g. "en"
MAIN_MENU_TEMPLATE = os.environ.get("MAIN_MENU_TEMPLATE", "main_menu_v2")


@app.route("/webhook", methods=["GET"])
def verify():
    # Facebook/WhatsApp/1msg verification handshake
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification token mismatch", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    # First, get the JSON from the request
    payload = request.get_json(force=True)

    # If payload is a string (double‐encoded JSON), decode it once more:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception as e:
            # If parsing fails, just log and return 200
            print("[WARN] Could not json.loads(payload):", e, "payload was:", payload)
            return Response(status=200)

    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # ───────────────────────────────────────────────────────────
    # 1) Try “Facebook‐style” nested format:
    #    payload["entry"][0]["changes"][0]["value"]["messages"]
    # ───────────────────────────────────────────────────────────
    messages = []
    from_whatsapp = False

    if "entry" in payload and isinstance(payload["entry"], list):
        entry   = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})
        messages = value.get("messages", [])
        from_whatsapp = True

    # ───────────────────────────────────────────────────────────
    # 2) Otherwise check if this is 1msg’s “direct” format:
    #    payload["messages"] is a top‐level array
    # ───────────────────────────────────────────────────────────
    elif "messages" in payload and isinstance(payload["messages"], list):
        messages = payload["messages"]
        from_whatsapp = True

    # If no messages found, just return 200
    if not messages:
        return Response(status=200)

    # ───────────────────────────────────────────────────────────
    # 3) Extract the first message object
    # ───────────────────────────────────────────────────────────
    message = messages[0]

    # Depending on source, “from” phone might be under message["from"] or message["author"]
    raw_from = ""
    if "from" in message:
        raw_from = message.get("from", "")
    elif "author" in message:
        raw_from = message.get("author", "")
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from

    # Determine message type & text body
    msg_type = message.get("type", "")
    text_body = ""

    # If it’s “Facebook‐style text”: message["text"]["body"]
    if msg_type == "text" and "text" in message:
        text_body = message["text"]["body"].strip().lower()

    # If it’s 1msg’s format for a plain chat: message["type"] == "chat"
    elif msg_type == "chat" and "body" in message:
        text_body = message["body"].strip().lower()
        msg_type = "text"  # normalize it

    # ───────────────────────────────────────────────────────────
    # 4) Handle “reset”
    # ───────────────────────────────────────────────────────────
    if msg_type == "text" and text_body == "reset":
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send main_menu_v2 template
        send_template_message(
            to=from_number,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=["there"]
        )
        return Response(status=200)

    # ───────────────────────────────────────────────────────────
    # 5) Handle quick‐reply BUTTON payloads
    #    - Facebook style: msg_type == "button" with nested message["button"]["payload"]
    #    - 1msg style minimal: msg_type == "button" but no nested "button"
    #    - 1msg style interactive: msg_type == "interactive" with interactive.button_reply.id
    # ───────────────────────────────────────────────────────────
    if msg_type == "button":
        # First, check nested "button" structure
        if "button" in message and isinstance(message["button"], dict) and "payload" in message["button"]:
            button_id = message["button"]["payload"]
        else:
            # Fallback to raw "body" text
            button_id = message.get("body", "").strip().lower()

        button_id = button_id.lower()

        if button_id in ["help_pest", "need help on pest!"]:
            set_user_state("car", from_number, {})
            return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

        if button_id in ["help_mold", "need help on mold!"]:
            set_user_state("mold", from_number, {})
            return handle_mold_flow(from_number, message, API_KEY, BASE_URL)

        if button_id in ["live_human", "live human"]:
            send_text_message({
                "to": from_number,
                "type": "text",
                "text": {"body": "Sure—one of our agents will be with you shortly."},
                "messaging_product": "whatsapp"
            })
            return Response(status=200)

        # Unrecognized button fallback
        send_text_message({
            "to": from_number,
            "type": "text",
            "text": {"body": "Sorry, I didn’t understand that selection. Type ‘reset’ to start over."},
            "messaging_product": "whatsapp"
        })
        return Response(status=200)

    # 1msg’s “interactive” style with button_reply (better than “button”)
    if msg_type == "interactive" and "interactive" in message:
        ir = message["interactive"]
        if ir.get("type") == "button_reply" and "button_reply" in ir:
            button_id = ir["button_reply"].get("id", "").strip().lower()
            if button_id in ["help_pest"]:
                set_user_state("car", from_number, {})
                return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)
            if button_id in ["help_mold"]:
                set_user_state("mold", from_number, {})
                return handle_mold_flow(from_number, message, API_KEY, BASE_URL)
            if button_id in ["live_human"]:
                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "text": {"body": "Sure—one of our agents will be with you shortly."},
                    "messaging_product": "whatsapp"
                })
                return Response(status=200)

            # Unrecognized interactive payload
            send_text_message({
                "to": from_number,
                "type": "text",
                "text": {"body": "Sorry, I didn’t understand that button. Type ‘reset’ to start over."},
                "messaging_product": "whatsapp"
            })
            return Response(status=200)

    # ───────────────────────────────────────────────────────────
    # 6) Delegate to flows if user is mid‐flow
    # ───────────────────────────────────────────────────────────
    user_state_car = get_user_state("car", from_number)
    if user_state_car:
        return handle_car_fumigation_flow(from_number, message, API_KEY, BASE_URL)

    user_state_bedbug = get_user_state("bedbug", from_number)
    if user_state_bedbug:
        return handle_bedbug_flow(from_number, message, API_KEY, BASE_URL)

    user_state_mold = get_user_state("mold", from_number)
    if user_state_mold:
        return handle_mold_flow(from_number, message, API_KEY, BASE_URL)

    # ───────────────────────────────────────────────────────────
    # 7) Otherwise, any other text → show main menu template
    # ───────────────────────────────────────────────────────────
    if msg_type == "text":
        send_template_message(
            to=from_number,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=["there"]
        )
        return Response(status=200)

    return Response(status=200)
# end dispatcher.py
