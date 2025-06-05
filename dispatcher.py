import os
import json
from flask import Flask, request, Response

from helpers import (
    send_text_message,
    send_interactive_message,
    send_template_message,  # ← for main_menu_v2
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

# ───── Webhook verification ─────
@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification token mismatch", 403

# ───── Main webhook endpoint (POST) ─────
@app.route("/webhook", methods=["POST"])
def receive_message():
    payload = request.get_json(force=True)
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # ─── Extract messages array ───
    messages = None
    if isinstance(payload.get("entry"), list):
        # Standard 1msg wrapper
        entry   = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})
        messages = value.get("messages", [])
    elif isinstance(payload.get("messages"), list):
        # Dev‐kit format: top‐level "messages": [...]
        messages = payload.get("messages", [])
    else:
        messages = []

    if not messages:
        return Response(status=200)

    # We only handle the first message in this example
    message_raw = messages[0]

    # Normalize “from” vs “author”
    raw_from = message_raw.get("from") or message_raw.get("author") or ""
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from

    msg_type = message_raw.get("type", "")

    # ───── Normalize body_text (for “chat”, “text”, or fallback) ─────
    body_text = ""
    if "text" in message_raw and isinstance(message_raw["text"], dict):
        body_text = message_raw["text"].get("body", "").strip().lower()
    elif "body" in message_raw:
        body_text = message_raw["body"].strip().lower()

    # ─────── 1) “reset” check ───────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text=='reset'), msg_type=", msg_type)

        # Clear all flow states
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send approved main_menu_v2 template via send_template_message()
        send_template_message(
            to=from_number,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    # ─────── 2) “button” presses ───────
    if msg_type == "button":
        # Attempt to read the “button” object; if missing, map via body_text
        if "button" in message_raw:
            button_id = message_raw["button"].get("payload", "")
        else:
            # Map common button titles (lowercased) → payload IDs
            if body_text == "need help on pest!":
                button_id = "help_pest"
            elif body_text == "need help on mold!":
                button_id = "help_mold"
            elif body_text == "live human":
                button_id = "live_human"
            else:
                button_id = ""

        print(f"[DEBUG] BUTTON payload = {button_id}")

        # If we deduced a payload_id but “button” key was missing, inject it now:
        if "button" not in message_raw and button_id:
            message_raw["button"] = {"payload": button_id}

        # Route to appropriate flow or response
        if button_id == "help_pest":
            set_user_state("car", from_number, {})  # start Car Fumigation flow
            return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)

        if button_id == "help_mold":
            set_user_state("mold", from_number, {})  # start Mold flow
            return handle_mold_flow(from_number, message_raw, API_KEY, BASE_URL)

        if button_id == "live_human":
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "Sure—one of our agents will be with you shortly." }
            })
            return Response(status=200)

    # ─────── 3‒5) Resume existing flow if any ───────
    if get_user_state("car", from_number) is not None:
        return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)

    if get_user_state("bedbug", from_number) is not None:
        return handle_bedbug_flow(from_number, message_raw, API_KEY, BASE_URL)

    if get_user_state("mold", from_number) is not None:
        return handle_mold_flow(from_number, message_raw, API_KEY, BASE_URL)

    # ─────── 6) Fallback: any other “text”/“chat”/“unsupported” → main menu ───────
    # If msg_type is “text”, “chat”, “unsupported” or any non‐empty body_text, re‐send main menu
    if msg_type in ("text", "chat", "unsupported") or body_text:
        print("[DEBUG] Falling back to show main menu for:", body_text, "msg_type=", msg_type)
        send_template_message(
            to=from_number,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    return Response(status=200)

# ───── End of dispatcher.py ─────
