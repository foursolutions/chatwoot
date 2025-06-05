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

# ────────────────────────────────────────────────────────────────────────────────
# Environment & Verification
# ────────────────────────────────────────────────────────────────────────────────
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
API_KEY      = os.environ.get("WHATSAPP_TOKEN", "")
BASE_URL     = "https://api.1msg.io/VAN388218473"


@app.route("/webhook", methods=["GET"])
def verify():
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return Response(challenge, status=200)
    return Response("Verification token mismatch", status=403)


@app.route("/webhook", methods=["POST"])
def receive_message():
    payload = request.get_json(force=True)
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # ────────────────────────────────────────────────────────────────────────────
    # Extract “messages” array
    # ────────────────────────────────────────────────────────────────────────────
    messages = []
    if isinstance(payload.get("entry"), list):
        entry   = payload["entry"][0]
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

    # ────────────────────────────────────────────────────────────────────────────
    # Get “from_number” (plain digits, no “@c.us”)
    # ────────────────────────────────────────────────────────────────────────────
    raw_from = message_raw.get("from") or message_raw.get("author") or ""
    if "@" in raw_from:
        from_number = raw_from.split("@")[0]
    else:
        from_number = raw_from

    # ────────────────────────────────────────────────────────────────────────────
    # Determine msg_type and body_text (lowercase) for text/chat
    # ────────────────────────────────────────────────────────────────────────────
    msg_type = message_raw.get("type", "")
    body_text = ""
    if msg_type in ("text", "chat") or "body" in message_raw:
        body_text = message_raw.get("body", "").strip().lower()
        if msg_type == "text" and isinstance(message_raw.get("text"), dict):
            body_text = message_raw["text"].get("body", "").strip().lower()

    # ────────────────────────────────────────────────────────────────────────────
    # (1) “reset” → clear states & send main menu template
    # ────────────────────────────────────────────────────────────────────────────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text == 'reset'), msg_type=", msg_type)
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        send_template_message(
            to=from_number,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────
    # (2) Button presses
    # ────────────────────────────────────────────────────────────────────────────
    if msg_type == "button":
        btn_text = message_raw.get("body", "").strip().lower()
        print("[DEBUG] BUTTON text =", btn_text)

        if btn_text == "need help on pest!":
            set_user_state("car", from_number, {})
            return handle_car_fumigation_flow(from_number + "@c.us", message_raw, API_KEY, BASE_URL)

        if btn_text == "need help on mold!":
            set_user_state("mold", from_number, {})
            return handle_mold_flow(from_number + "@c.us", message_raw, API_KEY, BASE_URL)

        if btn_text == "live human":
            send_text_message({
                "to": from_number + "@c.us",
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "Sure—one of our agents will be with you shortly." }
            })
            return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────
    # (3) Already in “car” flow? Delegate
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("car", from_number) is not None:
        return handle_car_fumigation_flow(from_number + "@c.us", message_raw, API_KEY, BASE_URL)

    # ────────────────────────────────────────────────────────────────────────────
    # (4) Already in “bedbug” flow? Delegate
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("bedbug", from_number) is not None:
        return handle_bedbug_flow(from_number + "@c.us", message_raw, API_KEY, BASE_URL)

    # ────────────────────────────────────────────────────────────────────────────
    # (5) Already in “mold” flow? Delegate
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("mold", from_number) is not None:
        return handle_mold_flow(from_number + "@c.us", message_raw, API_KEY, BASE_URL)

    # ────────────────────────────────────────────────────────────────────────────
    # (6) Free-text outside any flow: do nothing (200 OK)
    #     (If you prefer, uncomment the short fallback below.)
    # ────────────────────────────────────────────────────────────────────────────
    # send_text_message({
    #     "to": from_number + "@c.us",
    #     "type": "text",
    #     "messaging_product": "whatsapp",
    #     "text": { "body": "Sorry, I didn’t understand that. Type 'reset' to see the main menu again." }
    # })
    return Response(status=200)


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)

