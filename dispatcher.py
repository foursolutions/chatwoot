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
        # 1msg v2 format: payload["entry"][0]["changes"][0]["value"]["messages"]
        entry   = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})
        messages = value.get("messages", [])
    elif isinstance(payload.get("messages"), list):
        # 1msg v1 / dev-kit: top-level "messages": [...]
        messages = payload.get("messages", [])
    else:
        messages = []

    if not messages:
        return Response(status=200)

    # We handle only the first message in this example
    message_raw = messages[0]

    # ── Normalize “from” field ──
    # 1msg sometimes uses "from", sometimes "author". We normalize it.
    raw_from = message_raw.get("from") or message_raw.get("author") or ""
    message_raw["from"] = raw_from
    # Now every downstream handler can call message["from"]

    # ── Normalize body_text (for “chat”, “text”, etc.) ──
    body_text = ""
    if "text" in message_raw and isinstance(message_raw["text"], dict):
        body_text = message_raw["text"].get("body", "").strip().lower()
    elif "body" in message_raw:
        body_text = message_raw["body"].strip().lower()

    msg_type = message_raw.get("type", "")

    # ─────── 1) “reset” check ───────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text=='reset'), msg_type=", msg_type)
        # Clear all flow states:
        clear_user_state("car", raw_from)
        clear_user_state("bedbug", raw_from)
        clear_user_state("mold", raw_from)

        # Send main_menu_v2 template back via 1msg
        template_payload = {
            "token":    os.environ.get("1MSG_API_KEY"),
            "namespace": os.environ.get("1MSG_NAMESPACE"),
            "template":  "main_menu_v2",
            "language": {
                "policy": "deterministic",
                "code":   "en"
            },
            "params": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": ""}  # placeholder for greeting
                    ]
                }
            ],
            # "phone" must be digits‐only (no "@c.us")
            "phone": raw_from.split("@")[0]
        }
        send_interactive_message(template_payload)
        return Response(status=200)

    # ─────── 2) “button” presses ───────
    if msg_type == "button":
        button_id = message_raw["button"].get("payload", "")
        print(f"[DEBUG] BUTTON payload = {button_id}")

        if button_id == "help_pest":
            set_user_state("car", raw_from, {})
            return handle_car_fumigation_flow(raw_from, message_raw, API_KEY, BASE_URL)
        if button_id == "help_mold":
            set_user_state("mold", raw_from, {})
            return handle_mold_flow(raw_from, message_raw, API_KEY, BASE_URL)
        if button_id == "live_human":
            # Handoff to a live agent
            send_text_message({
                "to": raw_from.split("@")[0],
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Sure—one of our agents will be with you shortly."}
            })
            return Response(status=200)

    # ─────── 3) Already in “car” flow? ───────
    if get_user_state("car", raw_from) is not None:
        return handle_car_fumigation_flow(raw_from, message_raw, API_KEY, BASE_URL)

    # ─────── 4) Already in “bedbug” flow? ───────
    if get_user_state("bedbug", raw_from) is not None:
        return handle_bedbug_flow(raw_from, message_raw, API_KEY, BASE_URL)

    # ─────── 5) Already in “mold” flow? ───────
    if get_user_state("mold", raw_from) is not None:
        return handle_mold_flow(raw_from, message_raw, API_KEY, BASE_URL)

    # ─────── 6) Fallback: show main menu for any other text/chat/unsupported ───────
    if msg_type in ("text", "chat", "unsupported") or body_text:
        print("[DEBUG] Falling back to show main menu for:", body_text, "msg_type=", msg_type)
        template_payload = {
            "token":    os.environ.get("1MSG_API_KEY"),
            "namespace": os.environ.get("1MSG_NAMESPACE"),
            "template":  "main_menu_v2",
            "language": {
                "policy": "deterministic",
                "code":   "en"
            },
            "params": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": ""}
                    ]
                }
            ],
            "phone": raw_from.split("@")[0]
        }
        send_interactive_message(template_payload)
        return Response(status=200)

    return Response(status=200)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
