# dispatcher.py
from flask import Flask, request, jsonify
import os
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_template_message,
    send_list_message
)

app = Flask(__name__)

MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")

@app.route("/verify", methods=["GET"])
def verify():
    # standard Webhook verification (1msg handshake):
    # 1msg will GET /verify?hub.verify_token=<VERIFY_TOKEN>&hub.challenge=<challenge>
    # you respond with hub.challenge if token matches
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == os.getenv("VERIFY_TOKEN"):
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    # data["messages"] is a list; we take the first element for simplicity
    if "messages" not in data or len(data["messages"]) == 0:
        return jsonify({}), 200

    msg = data["messages"][0]
    chat_id = msg.get("chatId")  # e.g. "6589123456@c.us"
    msg_type = msg.get("type")   # e.g. "text" or "button_reply" etc.

    # Extract the incoming text body (for text messages)
    incoming_text = ""
    if msg_type == "text":
        incoming_text = msg["text"]["body"].strip().lower()
    # If it’s a button reply (in 1msg’s format), they send:
    #   msg_type == "button_reply"
    #   msg["button_reply"]["id"]   # the ID you set when sending the button
    #   msg["button_reply"]["title"]# the label
    elif msg_type == "button_reply":
        incoming_text = msg["button_reply"].get("id", "").lower()

    # 2. If user typed "reset", we clear all state and fire main menu template
    if incoming_text == "reset":
        # Optionally clear each flow’s state prefix. For example:
        clear_user_state("CAR_FUM", chat_id)
        clear_user_state("MOLD", chat_id)
        clear_user_state("BEDBUG", chat_id)
        # ... any other prefixes you have

        # Now send the main menu template
        # We assume main_menu_v2 has no params (or maybe a single param for {{1}} = user’s name)
        # Example: ["Nate"] if main_menu_v2 expects a name placeholder
        try:
            send_template_message(to=chat_id, template_name=MAIN_MENU_TEMPLATE, template_params=[])
        except Exception as e:
            print("❌ Failed to send main_menu_v2:", e)
        return jsonify({}), 200

    # 3. Otherwise, route into the correct flow based on user_state or button ID
    # For example, if the user is currently in CAR_FUM flow, call:
    #   flows/car_fumigation.handle_car_fumigation_flow(chat_id, msg)
    # If user just clicked “Car Fumigation” in main menu, that might appear as a button_reply id of "car_fum"
    #
    # Example (very simplified):
    state = get_user_state("CURRENT_FLOW", chat_id).get("flow_name")
    if state == "CAR_FUM":
        from flows.car_fumigation import handle_car_fumigation_flow
        handle_car_fumigation_flow(chat_id, msg)
    elif state == "MOLD":
        from flows.mold import handle_mold_flow
        handle_mold_flow(chat_id, msg)
    #  ...
    else:
        # If no state yet, interpret incoming_text or button ID as “pick a flow”
        # e.g. incoming_text == "car_fum" or a button id that your main_menu_v2 template used.
        if incoming_text == "car_fum":
            set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "CAR_FUM"})
            from flows.car_fumigation import handle_car_fumigation_flow
            handle_car_fumigation_flow(chat_id, msg)
        elif incoming_text == "mold":
            set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "MOLD"})
            from flows.mold import handle_mold_flow
            handle_mold_flow(chat_id, msg)
        # ... etc
        else:
            # If we don’t know what they typed, re‐send main menu
            send_template_message(to=chat_id, template_name=MAIN_MENU_TEMPLATE, template_params=[])
    return jsonify({}), 200


if __name__ == "__main__":
    # For local testing; in production Heroku will run via gunicorn
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
