import logging
from flask import Flask, request, jsonify, make_response

import flows.mold
import flows.bedbug
import flows.car_fumigation

from helpers import (
    send_text_message,
    send_template_message,
    send_main_menu_template,
    get_user_state,
    set_user_state,
    clear_user_state,
)

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payload = request.json
        logging.debug(f"🔍 Received webhook data: {payload}")

        # Skip if no messages present (e.g., ACKs or delivery updates)
        if "messages" not in payload or not payload["messages"]:
            return make_response(jsonify({}), 200)

        msg = payload["messages"][0]
        chat_id = msg.get("chatId")
        msg_type = msg.get("type")
        incoming_text = msg.get("body", "").strip().lower()

        logging.debug(f"🔍 chat_id = {chat_id}, type = {msg_type}")
        logging.debug(f"🔍 incoming_text = '{incoming_text}'")

        # RESET COMMAND
        if incoming_text == "reset":
            logging.info(f"ℹ️ Reset command detected for {chat_id}")
            clear_user_state(chat_id)
            send_main_menu_template(to=chat_id)
            return make_response(jsonify({}), 200)

        # ROUTE MAIN MENU BUTTONS (TEXT / BUTTONS)
        if incoming_text in ["need help on pest!", "need help on mold!", "live human"]:
            if incoming_text == "need help on pest!":
                logging.info(f"ℹ️ Starting Car Fumigation flow for {chat_id}")
                set_user_state(chat_id, {"flow": "car_fumigation", "step": "initial"})
                flows.car_fumigation.send_pest_control_list(to=chat_id)
            elif incoming_text == "need help on mold!":
                logging.info(f"ℹ️ Starting Mold flow for {chat_id}")
                set_user_state(chat_id, {"flow": "mold", "step": "initial"})
                flows.mold.start_mold_flow(chat_id)
            elif incoming_text == "live human":
                send_text_message(chat_id, "Please wait, a human agent will be with you shortly.")
            return make_response(jsonify({}), 200)

        # CONTINUE EXISTING FLOW
        state = get_user_state(chat_id)
        if state:
            flow = state.get("flow")
            if flow == "car_fumigation":
                flows.car_fumigation.handle_car_fumigation_flow(chat_id, msg, state)
            elif flow == "bedbug":
                flows.bedbug.handle_bedbug_flow(chat_id, msg, state)
            elif flow == "mold":
                flows.mold.handle_mold_flow(chat_id, msg, state)
            else:
                send_text_message(chat_id, "Sorry, unknown flow. Type 'reset' to start over.")
        else:
            logging.warning("⚠️ No active flow or command matched. Re-sending main menu.")
            send_main_menu_template(to=chat_id)

        return make_response(jsonify({}), 200)

    except Exception as e:
        logging.error("Error in webhook handler", exc_info=True)
        return make_response("Internal Server Error", 500)
