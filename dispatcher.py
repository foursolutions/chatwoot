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

# ─── Environment variables ───
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
API_KEY      = os.environ.get("WHATSAPP_TOKEN", "")
# Replace with your 1msg instance ID / base URL if different:
BASE_URL     = "https://api.1msg.io/VAN388218473"


# ────────────────────────────────────────────────────────────────────────────────
# 1) Webhook verification (GET /webhook)
#    Returns the hub.challenge when the VERIFY_TOKEN matches.
# ────────────────────────────────────────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return Response(challenge, status=200)
    return Response("Verification token mismatch", status=403)


# ────────────────────────────────────────────────────────────────────────────────
# 2) Message receiver (POST /webhook)
#    Parses incoming JSON, extracts the first message, and routes accordingly.
# ────────────────────────────────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def receive_message():
    payload = request.get_json(force=True)
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # ─── Extract the "messages" array from the payload ───
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
        # Nothing to process
        return Response(status=200)

    # We'll only process the first message in this webhook call:
    message_raw = messages[0]

    # ────────────────────────────────────────────────────────────────────────────────
    # Extract sender phone number as a plain string of digits (no "@c.us" suffix)
    # ────────────────────────────────────────────────────────────────────────────────
    raw_from    = message_raw.get("from") or message_raw.get("author") or ""
    if "@" in raw_from:
        from_number = raw_from.split("@")[0]
    else:
        from_number = raw_from

    # ────────────────────────────────────────────────────────────────────────────────
    # Determine message type and, if applicable, body_text (lowercased) for “text/chat”
    # ────────────────────────────────────────────────────────────────────────────────
    msg_type = message_raw.get("type", "")
    body_text = ""
    if msg_type in ("text", "chat") or "body" in message_raw:
        # For many WA payloads, the text sits under message_raw["body"]
        body_text = message_raw.get("body", "").strip().lower()
        # Some structures nest under message_raw["text"]["body"]
        if msg_type == "text" and isinstance(message_raw.get("text"), dict):
            body_text = message_raw["text"].get("body", "").strip().lower()

    # ────────────────────────────────────────────────────────────────────────────────
    # 2a) “reset” keyword always clears all flows & sends the main menu template
    # ────────────────────────────────────────────────────────────────────────────────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text == 'reset'), msg_type=", msg_type)
        # Clear any saved flow state for this user:
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send the main menu template (main_menu_v2) with one placeholder (“there”)
        send_template_message(
            to=from_number,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────────
    # 2b) Button presses
    #    If msg_type == "button", WhatsApp puts the tapped-button text into
    #    message_raw["body"] (and msg_type == "button").
    # ────────────────────────────────────────────────────────────────────────────────
    if msg_type == "button":
        btn_text = message_raw.get("body", "").strip().lower()
        print("[DEBUG] BUTTON text =", btn_text)

        # ───── “Need help on Pest!” → start car fumigation flow ─────
        if btn_text == "need help on pest!":
            # Initialize (empty) state for the “car” flow and delegate:
            set_user_state("car", from_number, {})
            return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)

        # ───── “Need help on Mold!” → start mold flow ─────
        if btn_text == "need help on mold!":
            set_user_state("mold", from_number, {})
            return handle_mold_flow(from_number, message_raw, API_KEY, BASE_URL)

        # ───── “Live Human” → send a quick confirmation message ─────
        if btn_text == "live human":
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Sure—one of our agents will be with you shortly."}
            })
            return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────────
    # 3) If the user is already in the “car” flow, delegate to handle_car_fumigation_flow
    # ────────────────────────────────────────────────────────────────────────────────
    if get_user_state("car", from_number) is not None:
        return handle_car_fumigation_flow(from_number, message_raw, API_KEY, BASE_URL)

    # ────────────────────────────────────────────────────────────────────────────────
    # 4) If the user is in the “bedbug” flow, delegate to handle_bedbug_flow
    # ────────────────────────────────────────────────────────────────────────────────
    if get_user_state("bedbug", from_number) is not None:
        return handle_bedbug_flow(from_number, message_raw, API_KEY, BASE_URL)

    # ────────────────────────────────────────────────────────────────────────────────
    # 5) If the user is in the “mold” flow, delegate to handle_mold_flow
    # ────────────────────────────────────────────────────────────────────────────────
    if get_user_state("mold", from_number) is not None:
        return handle_mold_flow(from_number, message_raw, API_KEY, BASE_URL)

    # ────────────────────────────────────────────────────────────────────────────────
    # 6) Any other free‐text/outside‐flow: do nothing (200 OK with empty body).
    #    If you prefer, you can uncomment the short fallback message below.
    # ────────────────────────────────────────────────────────────────────────────────
    # send_text_message({
    #     "to": from_number,
    #     "type": "text",
    #     "messaging_product": "whatsapp",
    #     "text": {
    #         "body": "Sorry, I didn’t understand that. Type 'reset' to see the main menu again."
    #     }
    # })
    return Response(status=200)


# ────────────────────────────────────────────────────────────────────────────────
# 3) Run the Flask app
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)

