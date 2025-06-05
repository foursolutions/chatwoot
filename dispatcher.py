# dispatcher.py

import os
import json
from flask import Flask, request, Response

from helpers import (
    send_text_message,
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
# Environment & Webhook Verification
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
    # 1) Extract the “messages” array (standard WhatsApp + 1msg wrapper)
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

    # We only care about the very first message in this call:
    message_raw = messages[0]

    # ────────────────────────────────────────────────────────────────────────────
    # 2) Extract the sender phone number in plain‐digits format (no “@c.us”)
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
    if msg_type in ("text", "chat") or "body" in message_raw:
        body_text = message_raw.get("body", "").strip().lower()
        if msg_type == "text" and isinstance(message_raw.get("text"), dict):
            body_text = message_raw["text"].get("body", "").strip().lower()

    # ────────────────────────────────────────────────────────────────────────────
    # 4) “reset” → clear all flows and immediately send main menu template
    # ────────────────────────────────────────────────────────────────────────────
    if body_text == "reset":
        print("[DEBUG] RESET branch hit (body_text == 'reset'), msg_type=", msg_type)

        # Clear every flow’s state for this user
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send the main_menu_v2 template. Note: pass “to=from_number” (plain digits).
        send_template_message(
            to=from_number,               # e.g. "6587788080"
            template_name="main_menu_v2", # your pre‐approved template name
            template_params=["there"]     # that single placeholder
        )

        # Immediately return—no further logic in this request
        return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────
    # 5) Button presses: route “Need help on Pest!”, “Need help on Mold!”, “Live Human”
    # ────────────────────────────────────────────────────────────────────────────
    if msg_type == "button":
        btn_text = message_raw.get("body", "").strip().lower()
        print("[DEBUG] BUTTON text =", btn_text)

        # “Need help on Pest!” → start the Car Fumigation flow
        if btn_text == "need help on pest!":
            # Initialize the “car” flow with an empty state
            set_user_state("car", from_number, {})

            # We pass to handle_car_fumigation_flow the FULL chatId (with "@c.us"),
            # because that flow will call send_list_message(to_chat_id).
            return handle_car_fumigation_flow(
                to_chat_id=from_number + "@c.us",
                message=message_raw,
                api_key=API_KEY,
                base_url=BASE_URL
            )

        # “Need help on Mold!” → start the Mold flow
        if btn_text == "need help on mold!":
            set_user_state("mold", from_number, {})
            return handle_mold_flow(
                to_chat_id=from_number + "@c.us",
                message=message_raw,
                api_key=API_KEY,
                base_url=BASE_URL
            )

        # “Live Human” → send a simple text confirming an agent is on the way
        if btn_text == "live human":
            send_text_message({
                "to": from_number,  # plain digits
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {
                    "body": "Sure—one of our agents will be with you shortly."
                }
            })
            return Response(status=200)

    # ────────────────────────────────────────────────────────────────────────────
    # 6) If already in the “car” flow, delegate to that handler
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("car", from_number) is not None:
        return handle_car_fumigation_flow(
            to_chat_id=from_number + "@c.us",
            message=message_raw,
            api_key=API_KEY,
            base_url=BASE_URL
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 7) If already in the “bedbug” flow, delegate
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("bedbug", from_number) is not None:
        return handle_bedbug_flow(
            to_chat_id=from_number + "@c.us",
            message=message_raw,
            api_key=API_KEY,
            base_url=BASE_URL
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 8) If already in the “mold” flow, delegate
    # ────────────────────────────────────────────────────────────────────────────
    if get_user_state("mold", from_number) is not None:
        return handle_mold_flow(
            to_chat_id=from_number + "@c.us",
            message=message_raw,
            api_key=API_KEY,
            base_url=BASE_URL
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 9) Free‐text outside any flow: do nothing (200 OK)
    #    (If you’d rather send a hint, uncomment the send_text_message below)
    # ────────────────────────────────────────────────────────────────────────────
    # send_text_message({
    #     "to": from_number,
    #     "type": "text",
    #     "messaging_product": "whatsapp",
    #     "text": {
    #         "body": "I didn’t understand that. Type ‘reset’ to see the main menu again."
    #     }
    # })
    return Response(status=200)


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)
