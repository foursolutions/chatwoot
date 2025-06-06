# dispatcher.py

import os
import logging
from flask import Flask, request, jsonify, make_response

from helpers import (
    send_text_message,
    send_template_message,
    get_user_state,
    set_user_state,
    clear_user_state
)

import flows.mold
import flows.bedbug
import flows.car_fumigation

app = Flask(__name__)

REDIS_PREFIX_MOLD = "mold"
REDIS_PREFIX_BED = "bedbug"
REDIS_PREFIX_CAR = "carfum"
MAIN_MENU_TEMPLATE = "main_menu_v2"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json()
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return make_response("No messages to process", 200)

        message = messages[0]
        from_number = message["from"]
        msg_type = message.get("type")

        # ───────────────────────────────
        # 1) TEXT MESSAGES
        # ───────────────────────────────
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()
            print(f"[DEBUG] Received TEXT from {from_number}: '{text_body}'")

            if text_body == "reset":
                print(f"[DEBUG] 'reset' detected for {from_number}. Clearing all states and sending main menu.")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                clear_user_state(REDIS_PREFIX_BED, from_number)

                car_fumigation.send_main_menu(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Reset: Main menu sent", 200)

            if text_body in ["need help on mold!", "need help on mold"]:
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                set_user_state(REDIS_PREFIX_MOLD, from_number, {"step": "mold_option", "affected_areas": []})
                mold.send_mold_option_prompt(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Mold flow started", 200)

            if text_body in ["need help on pest!", "need help on pest"]:
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_BED, from_number)
                set_user_state(REDIS_PREFIX_CAR, from_number, {"step": "choose_service"})
                car_fumigation.send_pest_control_list(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Pest flow started", 200)

            # Delegate based on current active flow state
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                mold.handle_mold_flow(from_number, message, state_mold)
                return make_response("Mold flow TEXT handled", 200)

            state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
            if state_bed:
                bedbug.handle_bedbug_flow(from_number, message, state_bed)
                return make_response("Bedbug flow TEXT handled", 200)

            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                car_fumigation.handle_car_fumigation_flow(from_number, message, state_car)
                return make_response("Car flow TEXT handled", 200)

            # Fallback
            send_text_message(to=from_number, body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin.")
            return make_response("No active flow & TEXT fallback sent", 200)

        # ───────────────────────────────
        # 2) INTERACTIVE or BUTTON TYPES
        # ───────────────────────────────
        if msg_type in ["interactive", "button"]:
            # Always check which flow is active
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                car_fumigation.handle_car_fumigation_flow(from_number, message, state_car)
                return make_response("Car flow INTERACTIVE handled", 200)

            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                mold.handle_mold_flow(from_number, message, state_mold)
                return make_response("Mold flow INTERACTIVE handled", 200)

            state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
            if state_bed:
                bedbug.handle_bedbug_flow(from_number, message, state_bed)
                return make_response("Bedbug flow INTERACTIVE handled", 200)

            # If no state is found
            send_text_message(to=from_number, body="Please type 'reset' to start.")
            return make_response("No state found for INTERACTIVE", 200)

    except Exception as e:
        logging.exception("Error in webhook handler")
        return make_response(f"Internal error: {e}", 500)
