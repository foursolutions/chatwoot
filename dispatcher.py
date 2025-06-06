from flask import Flask, request, jsonify
from flows import mold, bedbug, car_fumigation
from utils import normalize_text, clear_user_state, get_user_state, set_user_state
from helpers import send_text_message, send_template_message, send_main_menu_template
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

            # RESET FLOW
            if incoming_text == "reset":
                logging.info(f"ℹ️ Reset command detected. Clearing all flow states for: {chat_id}")
                clear_user_state("CAR_FUM", chat_id)
                clear_user_state("MOLD", chat_id)
                clear_user_state("BEDBUG", chat_id)
                logging.info(f"ℹ️ Sending main_menu_v2 template to {chat_id}")
                send_main_menu_template(chat_id)
                return jsonify({}), 200

            # DETERMINE CURRENT FLOW
            current_flow = get_user_state("CURRENT_FLOW", chat_id).get("flow_name", "")
            logging.debug(f"🔍 CURRENT_FLOW = {current_flow}")

            # ROUTE TO FLOW IF ACTIVE
            if current_flow == "CAR_FUM":
                return car_fumigation.receive_message(chat_id, msg)
            if current_flow == "MOLD":
                return mold.receive_message(chat_id, msg)
            if current_flow == "BEDBUG":
                return bedbug.receive_message(chat_id, msg)

            # MAIN MENU SELECTION (button/list/text entry)
            if incoming_text in ["car_fum", "need help on pest!", "car_fumigation"]:
                set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "CAR_FUM"})
                return car_fumigation.receive_message(chat_id, msg)

            if incoming_text in ["mold", "need help on mold!", "mold_check"]:
                set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "MOLD"})
                return mold.receive_message(chat_id, msg)

            if incoming_text in ["bedbug", "need help on bedbug!", "bedbug_check"]:
                set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "BEDBUG"})
                return bedbug.receive_message(chat_id, msg)

            # DEFAULT RESPONSE
            logging.warning(f"⚠️ Unknown input. Sending main menu to {chat_id}")
            send_main_menu_template(chat_id)
            return jsonify({}), 200

        return jsonify({"status": "no_message"}), 200

    except Exception as e:
        logging.error(f"❌ Error in receive_message: {e}")
        return jsonify({"error": str(e)}), 200


if __name__ == "__main__":
    app.run(debug=True)
