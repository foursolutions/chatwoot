from flask import Flask, request
from flows import mold, bedbug, car_fumigation
from helpers import (
    normalize_text,
    clear_user_state,
    get_user_state,
    set_user_state,
    send_text_message,
    send_template_message,
    send_main_menu_template
)
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        logging.debug(f"🔍 Received webhook data: {data}")

        if "messages" in data and data["messages"]:
            msg = data["messages"][0]
            chat_id = msg.get("chatId")
            msg_type = msg.get("type", "")
            incoming_text = normalize_text(msg.get("body", ""))

            logging.debug(f"🔍 chat_id = {chat_id}, type = {msg_type}")
            logging.debug(f"🔍 incoming_text (normalized) = '{incoming_text}'")

            # RESET command
            if incoming_text == "reset":
                clear_user_state(chat_id)
                logging.info(f"ℹ️ Reset command detected. Clearing all flow states for: {chat_id}")
                send_main_menu_template(chat_id)
                return "OK"

            # Route based on flow
            state_mold = get_user_state(chat_id, "mold")
            state_bedbug = get_user_state(chat_id, "bedbug")
            state_car = get_user_state(chat_id, "car_fumigation")

            if state_mold or incoming_text == "need help on mold!":
                logging.info(f"ℹ️ Starting Mold flow for {chat_id}")
                mold.handle_mold_flow(chat_id, msg, state_mold)
            elif state_bedbug or incoming_text == "need help on bedbug!":
                logging.info(f"ℹ️ Starting Bedbug flow for {chat_id}")
                bedbug.handle_bedbug_flow(chat_id, msg, state_bedbug)
            elif state_car or incoming_text == "need help on pest!":
                logging.info(f"ℹ️ Starting Car Fumigation flow for {chat_id}")
                car_fumigation.handle_car_fumigation_flow(chat_id, msg, state_car)
            else:
                logging.warning(f"⚠️ Unrecognized input: {incoming_text}")
                send_text_message(chat_id, "Sorry, I didn’t understand that. Type 'reset' to start over.")
        else:
            logging.warning("⚠️ No message found in webhook payload.")
    except Exception as e:
        logging.error(f"❌ Error in receive_message: {e}")
    return "OK"
