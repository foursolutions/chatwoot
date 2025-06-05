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
# Environment / Webhook Verification
# ────────────────────────────────────────────────────────────────────────────────
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
API_KEY      = os.environ.get("WHATSAPP_TOKEN", "")
BASE_URL     = "https://api.1msg.io/VAN388218473"  # your 1msg instance

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
    # 1) Extract “messages” array (standard WhatsApp + 1msg wrapper)
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
        # Nothing to do
        return Response(status=200)

    # We only process the first message in this webhook call:
    message_raw = messages[0]

    # ────────────────────────────────────────────────────────────────────────────
    # 2) Extract the sender’s phone number (plain digits, no “@c.us”)
    # ────────────────────────────────────────────────────────────────────────────
    raw_from = message_raw.get("from") or message_raw.get("author") or ""
    if "@" in raw_from:
        from_number = raw_from.split("@")[0]
    else:
        from_number = raw_from

    # ────────────────────────────────────────────────────────────────────────────
    # 3) Determine message type (button / text / interactive / etc.) and body_text
    # ────────────────────────────────────────────────────────────────────────────
    msg_type = message_raw.get("type", "")
    body_text = ""
    # If this is a plain chat/text message, normalize its body to lowercase
    if msg_type in ("text", "chat") or "body" in message_raw:
        body_text = message_raw.get("body", "").strip().lower()
        # Some payloads nest text under message_raw["text"]["body"]
        if msg_type == "text" and isinstance(message_raw.get("text"), dict):
            body_text = message_raw["text"].get("body", "").strip().lower()

    # ────────────────────────────────────────────────────────────────────────────
    # 4) “reset” keyword: always clear all flows and immediately send main menu
    # ────────────────────────────────────────────────────────────────────────────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text == 'reset'), msg_type=", msg_type)

        # Clear any saved flow‐state for this user (car, bedbug, mold)
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send the main menu template (main_menu_v2) with the one placeholder “there”
        #
        # IMPORTANT: send_template_message expects the phone as plain digits (no “@c.us”).
        send_template_message(
            to=from_number,               # e.g. "6587788080"
            template_name="main_menu_v2", # your approved template
            template_params=["there"]     # the one placeholder
        )

        # Immediately return—no further routing in this request
        return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────
    # 5) Button presses: route “Need help on Pest!”, “Need help on Mold!”, “Live Human”
    # ────────────────────────────────────────────────────────────────────────────
    if msg_type == "button":
        btn_text = message_raw.get("body", "").strip().lower()
        print("[DEBUG] BUTTON text =", btn_text)

        # ─── “Need help on Pest!” → start (or continue) the Car‐Fumigation flow
        if btn_text == "need help on pest!":
            # Initialize the “car” flow state (empty dict)
            set_user_state("car", from_number, {})

            # Pass in the **full chatId** (with “@c.us”) into the flow handler,
            # because inside we will use send_list_message(...) which needs the “@c.us”
            return handle_car_fumigation_flow(
                to=from_number + "@c.us",
                message=message_raw,
                api_key=API_KEY,
                base_url=BASE_URL
            )

        # ─── “Need help on Mold!” → start Mold flow
        if btn_text == "need help on mold!":
            set_user_state("mold", from_number, {})
            return handle_mold_flow(
                to=from_number + "@c.us",
                message=message_raw,
                api_key=API_KEY,
                base_url=BASE_URL
            )

        # ─── “Live Human” → send a quick text confirming a live agent will pick up
        if btn_text == "live human":
            send_text_message({
                "to": from_number + "@c.us",
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {
                    "body": "Sure—one of our agents will be with you shortly."
                }
            })
            return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────
    # 6) If the user is already in a “car” flow, delegate to that flow-handler
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("car", from_number) is not None:
        # We append “@c.us” here because all lists/interactive calls inside expect a full chatId.
        return handle_car_fumigation_flow(
            to=from_number + "@c.us",
            message=message_raw,
            api_key=API_KEY,
            base_url=BASE_URL
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 7) If the user is already in a “bedbug” flow, delegate
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("bedbug", from_number) is not None:
        return handle_bedbug_flow(
            to=from_number + "@c.us",
            message=message_raw,
            api_key=API_KEY,
            base_url=BASE_URL
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 8) If the user is already in a “mold” flow, delegate
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("mold", from_number) is not None:
        return handle_mold_flow(
            to=from_number + "@c.us",
            message=message_raw,
            api_key=API_KEY,
            base_url=BASE_URL
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 9) Fallback: Free-text outside of any active flow
    #    We choose to do **nothing** (200 OK) so that the bot does not re-send the main menu.
    #    If you prefer, you could send a short hint (“Type ‘reset’ to see main menu again.”).
    # ────────────────────────────────────────────────────────────────────────────
    return Response(status=200)


# ────────────────────────────────────────────────────────────────────────────────
# 10) Run the Flask app
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)


