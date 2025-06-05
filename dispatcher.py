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
from flows.bedbug         import handle_bedbug_flow
from flows.mold           import handle_mold_flow

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

    # ─── Extract the array of incoming messages ───
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

    # ────────────────────────────────────────────────────────────────
    # 1) Ignore any echo from WhatsApp/the provider itself ("fromMe": true or "self": 1)
    # ────────────────────────────────────────────────────────────────
    if message_raw.get("fromMe") or message_raw.get("self") == 1:
        return Response(status=200)

    # ────────────────────────────────────────────────────────────────
    # 2) Normalize the sender
    # ────────────────────────────────────────────────────────────────
    raw_from    = message_raw.get("from") or message_raw.get("author") or ""
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from

    # ────────────────────────────────────────────────────────────────
    # 3) Extract type + textual body (lowercased)
    # ────────────────────────────────────────────────────────────────
    msg_type  = message_raw.get("type", "")
    body_text = ""
    if "text" in message_raw and isinstance(message_raw["text"], dict):
        body_text = message_raw["text"].get("body", "").strip().lower()
    elif message_raw.get("body"):
        body_text = message_raw.get("body", "").strip().lower()

    # ────────────────────────────────────────────────────────────────
    # 4) “reset” branch: clear all state, then send main_menu_v2 (once)
    # ────────────────────────────────────────────────────────────────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text=='reset'), msg_type=", msg_type)

        clear_user_state("car",    from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold",   from_number)

        send_template_message(
            to=from_number,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    # ────────────────────────────────────────────────────────────────
    # 5) “button” presses (interactive buttons). 1MSG may send:
    #      { "type":"button", "body":"Need help on Pest!", … }
    #    rather than a nested message["button"]["payload"]. We therefore:
    #      • check for message_raw["button"]["payload"] if present, else
    #      • fall back to using raw body_text.
    # ────────────────────────────────────────────────────────────────
    if msg_type == "button":
        if "button" in message_raw and isinstance(message_raw["button"], dict):
            payload_id = message_raw["button"].get("payload", "").strip().lower()
        else:
            payload_id = body_text  # e.g. "need help on pest!", "need help on mold!", "live human"

        print(f"[DEBUG] BUTTON payload_id = {payload_id}")

        if payload_id == "need help on pest!":
            # → start Car Fumigation flow
            set_user_state("car", from_number, {})
            return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)

        if payload_id == "need help on mold!":
            # → start Mold flow
            set_user_state("mold", from_number, {})
            mold_state = get_user_state("mold", from_number)
            return handle_mold_flow(from_number, message_raw, mold_state)

        if payload_id == "need help on bedbugs!":
            # → start Bedbug flow (if your UI ever has that button)
            set_user_state("bedbug", from_number, {})
            bedbug_state = get_user_state("bedbug", from_number)
            return handle_bedbug_flow(from_number, message_raw, bedbug_state)

        if payload_id == "live human":
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Sure—one of our agents will be with you shortly."}
            })
            return Response(status=200)

    # ────────────────────────────────────────────────────────────────
    # 6) If we’re already in one of the flows, resume it
    # ────────────────────────────────────────────────────────────────
    state_car    = get_user_state("car",    from_number)
    state_bedbug = get_user_state("bedbug", from_number)
    state_mold   = get_user_state("mold",   from_number)

    if state_car is not None:
        return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)

    if state_bedbug is not None:
        return handle_bedbug_flow(from_number, message_raw, state_bedbug)

    if state_mold is not None:
        return handle_mold_flow(from_number, message_raw, state_mold)

    # ────────────────────────────────────────────────────────────────
    # 7) Fallback: any other chat/text → re‐send main_menu_v2 template
    # ────────────────────────────────────────────────────────────────
    if msg_type in ("text", "chat") and body_text:
        print("[DEBUG] Falling back to “show main menu” for:", body_text)
        send_template_message(
            to=from_number,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    return Response(status=200)

# ───── Run locally if this file is executed directly ─────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
