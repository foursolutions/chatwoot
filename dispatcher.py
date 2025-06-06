# dispatcher.py

import os
import json
from flask import Flask, request, make_response

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_interactive_message,
    send_text_message,
)

import flows.car_fumigation as car_fumigation
import flows.mold as mold
import flows.bedbug as bedbug

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

REDIS_PREFIX_CAR = "carfum"
REDIS_PREFIX_MOLD = "mold"
REDIS_PREFIX_BED = "bedbug"


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
    payload = request.get_json()
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return make_response("No messages", 200)

        message = messages[0]
        from_number = message["from"]
        msg_type = message.get("type", "")
        user_text = ""
        normalized_text = ""

        if msg_type == "text":
            user_text = message["text"]["body"]
            normalized_text = user_text.strip().lower()
            print(f"[DEBUG] TEXT from {from_number}: {normalized_text}")

            if normalized_text == "reset":
                print(f"[DEBUG] RESET received from {from_number}")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                clear_user_state(REDIS_PREFIX_BED, from_number)
                car_fumigation.send_main_menu(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Main menu sent", 200)

            if normalized_text in ["need help on pest!", "need help on pest"]:
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_BED, from_number)
                set_user_state(REDIS_PREFIX_CAR, from_number, {"step": "choose_service"})
                car_fumigation.send_pest_control_list(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Pest list sent", 200)

            if normalized_text == "need help on mold!":
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                set_user_state(REDIS_PREFIX_MOLD, from_number, {
                    "step": "mold_option",
                    "affected_areas": []
                })
                mold.send_mold_option_prompt(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Mold flow started", 200)

        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            i_type = interactive.get("type")

            # list_reply from pest control list
            if i_type == "list_reply":
                selected_id = interactive["list_reply"]["id"]
                print(f"[DEBUG] LIST selection: {selected_id}")
                user_state = get_user_state(REDIS_PREFIX_CAR, from_number)
                step = user_state.get("step", "") if user_state else ""

                if step == "choose_service":
                    if selected_id == "car_fumigation":
                        user_state = {"step": "select_pest_type"}
                        set_user_state(REDIS_PREFIX_CAR, from_number, user_state)
                        car_fumigation.send_pest_type_list(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                        return make_response("Car Fumigation menu sent", 200)
                    else:
                        send_text_message(to=from_number, body="Sorry, that option is not available yet.")
                        return make_response("Unhandled list option", 200)

        elif msg_type in ["button"]:
            payload = message.get("button", {}).get("payload", "").lower()
            print(f"[DEBUG] Button payload: {payload}")

            # Check if it's a mold flow button
            if payload == "need help on mold!":
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                set_user_state(REDIS_PREFIX_MOLD, from_number, {
                    "step": "mold_option",
                    "affected_areas": []
                })
                mold.send_mold_option_prompt(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Mold flow triggered via button", 200)

            # Check if it's a pest flow button
            if payload in ["need help on pest", "need help on pest!"]:
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_BED, from_number)
                set_user_state(REDIS_PREFIX_CAR, from_number, {"step": "choose_service"})
                car_fumigation.send_pest_control_list(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Pest flow triggered via button", 200)

        # fallback
        send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
        return make_response("Fallback sent", 200)

    except Exception as e:
        print("ERROR:root:Error in webhook handler")
        print(e)
        return make_response("Error occurred", 500)
