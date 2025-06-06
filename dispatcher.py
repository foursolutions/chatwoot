import os
import json
import logging
from flask import Flask, request, make_response

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_interactive_message,
    send_text_message,
)

import flows.mold
import flows.bedbug
import flows.car_fumigation

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return make_response(challenge, 200)
    else:
        return make_response("Verification token mismatch", 403)


@app.route("/webhook", methods=["POST"])
def receive_message():
    try:
        payload = request.json
        logging.debug("🔍 Received webhook data: %s", payload)

        entries = payload.get("entry", [])
        if not entries:
            raise ValueError("❌ 'entry' field missing or empty in payload")

        changes = entries[0].get("changes", [])
        if not changes:
            raise ValueError("❌ 'changes' field missing or empty in entry")

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return "ok", 200

        msg = messages[0]
        chat_id = msg.get("chatId") or msg.get("from")
        msg_type = msg.get("type", "")
        incoming_text = msg.get("body", "").strip().lower()

        logging.debug(f"🔍 chat_id = {chat_id}, type = {msg_type}")
        logging.debug(f"🔍 incoming_text = '{incoming_text}'")

        # Reset handler
        if incoming_text == "reset":
            clear_user_state(chat_id)
            logging.info(f"ℹ️ Reset command detected. Sending main menu to {chat_id}")
            send_template_message(chat_id, MAIN_MENU_TEMPLATE, {"greeting_name": "there"})
            return "ok", 200

        # Route to car fumigation flow (handles both button and list interactions)
        flows.car_fumigation.handle_car_fumigation_flow(chat_id, msg)

        return "ok", 200

    except Exception as e:
        logging.error("Error in webhook handler")
        logging.error(str(e))
        return make_response(str(e), 500)
