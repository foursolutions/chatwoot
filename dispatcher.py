# dispatcher.py

import os
from flask import Flask, request, Response

from helpers import get_user_state, set_user_state, clear_user_state
from flows.bedbug import handle_bedbug_flow
from flows.car_fumigation import handle_car_fumigation_flow
from flows.mold import handle_mold_flow

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    # Each incoming 1msg webhook will have “messages” array, etc.
    # We assume a single message per webhook push:
    message = data["messages"][0]
    from_number = message["chatId"]
    msg_type = message.get("type", "")

    # 1) Check for global “reset” (text exactly “reset” or button payload “reset”)
    body_text = ""
    if msg_type == "text":
        body_text = message.get("body", "").strip().lower()
    if msg_type == "button":
        body_text = message.get("body", "").strip().lower()

    if body_text == "reset":
        # Clear ALL user states across all flows
        clear_user_state("bedbug", from_number)
        clear_user_state("car", from_number)
        clear_user_state("mold", from_number)

        # Re-send the main menu template
        # Note: send_main_menu expects plain digits, so we split off “@c.us”.
        from flows.car_fumigation import send_main_menu
        send_main_menu(to=from_number.split("@")[0])
        return Response(status=200)

    # 2) Otherwise, dispatch based on which flow “owns” this conversation
    # Check if user already has a flow in progress:
    if get_user_state("bedbug", from_number):
        handle_bedbug_flow(from_number, message, get_user_state("bedbug", from_number))
        return Response(status=200)

    if get_user_state("car", from_number):
        handle_car_fumigation_flow(from_number, message, os.environ.get("WHATSAPP_TOKEN", ""), "https://api.1msg.io")
        return Response(status=200)

    if get_user_state("mold", from_number):
        handle_mold_flow(from_number, message, get_user_state("mold", from_number))
        return Response(status=200)

    # 3) If no flow in progress, check the first button they pressed from the main menu
    #    e.g. “Need help on Bedbugs!”, “Need help on Pest!” or “Need help on Mold!”
    if msg_type == "button":
        payload = message.get("body", "").strip().lower()
        if payload == "need help on bedbugs!":
            clear_user_state("bedbug", from_number)
            set_user_state("bedbug", from_number, { "step": "" })
            handle_bedbug_flow(from_number, message, {})
            return Response(status=200)

        if payload == "need help on pest!":
            # Start the Car flow at step “pest_control_list”
            state = { "step": "pest_control_list" }
            set_user_state("car", from_number, state)
            handle_car_fumigation_flow(from_number, message, os.environ.get("WHATSAPP_TOKEN", ""), "https://api.1msg.io")
            return Response(status=200)

        if payload == "need help on mold!":
            clear_user_state("mold", from_number)
            set_user_state("mold", from_number, { "step": "" })
            handle_mold_flow(from_number, message, {})
            return Response(status=200)

    # 4) Otherwise, unrecognized—just ignore or send a “type reset” prompt
    #    (you could also re-send the main menu here if you’d like)
    return Response(status=200)

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)

