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
        entry   = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})
        messages = value.get("messages", [])
    elif isinstance(payload.get("messages"), list):
        messages = payload.get("messages", [])
    else:
        messages = []

    if not messages:
        return Response(status=200)

    message_raw = messages[0]
    raw_from = message_raw.get("from") or message_raw.get("author") or ""
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from

    msg_type = message_raw.get("type", "")

    # ✅ Normalize body text from various formats (chat, text, etc.)
    body_text = ""
    if "text" in message_raw and "body" in message_raw["text"]:
        body_text = message_raw["text"]["body"].strip().lower()
    elif "body" in message_raw:
        body_text = message_raw["body"].strip().lower()

    # ─────── 1) “reset” check ───────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text=='reset'), msg_type=", msg_type)
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # ✅ Send approved main_menu_v2 template
        template_payload = {
            "to": from_number,
            "type": "template",
            "messaging_product": "whatsapp",
            "template": {
                "name": "main_menu_v2",
                "language": {
                    "code": "en",
                    "policy": "deterministic"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": "there"
                            }
                        ]
                    }
                ]
            }
        }
        send_interactive_message(template_payload)
        return Response(status=200)

    # ─────── 2) “button” presses ───────
    if msg_type == "button":
        button_id = message_raw["button"].get("payload", "")
        print(f"[DEBUG] BUTTON payload = {button_id}")
        if button_id == "help_pest":
            set_user_state("car", from_number, {})
            return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)
        if button_id == "help_mold":
            set_user_state("mold", from_number, {})
            return handle_mold_flow(from_number, message_raw, API_KEY, BASE_URL)
        if button_id == "live_human":
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "Sure—one of our agents will be with you shortly." }
            })
            return Response(status=200)

    # ─────── 3–5) Resume if in flow ───────
    if get_user_state("car", from_number) is not None:
        return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)
    if get_user_state("bedbug", from_number) is not None:
        return handle_bedbug_flow(from_number, message_raw, API_KEY, BASE_URL)
    if get_user_state("mold", from_number) is not None:
        return handle_mold_flow(from_number, message_raw, API_KEY, BASE_URL)

    # ─────── 6) Fallback: show main menu again ───────
    if msg_type in ("text", "chat") or body_text:
        print("[DEBUG] Falling back to show main menu for:", body_text, "msg_type=", msg_type)
        template_payload = {
            "to": from_number,
            "type": "template",
            "messaging_product": "whatsapp",
            "template": {
                "name": "main_menu_v2",
                "language": {
                    "code": "en",
                    "policy": "deterministic"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": "there"
                            }
                        ]
                    }
                ]
            }
        }
        send_interactive_message(template_payload)
        return Response(status=200)

    return Response(status=200)

# ───── End of dispatcher.py ─────
