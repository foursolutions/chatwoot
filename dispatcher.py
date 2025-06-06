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

from flows import car_fumigation
from flows import mold
from flows import bedbug

app = Flask(__name__)
VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")  # Not directly used in payloads

# Redis prefixes for flow-specific user states
REDIS_PREFIX_CAR  = "carfum"
REDIS_PREFIX_MOLD = "mold"
REDIS_PREFIX_BED  = "bedbug"

# Name of a fallback “echo” template (must exist and be approved in 360dialog)
ECHO_TEMPLATE = "echo_message_text"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # ======== Webhook Verification ========
    if request.method == "GET":
        mode      = request.args.get("hub.mode")
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return make_response(challenge, 200)
        return make_response("Verification token mismatch", 403)

    # ======== Incoming Messages ========
    payload = request.get_json()
    if not payload:
        return make_response("No JSON received", 400)

    entry   = payload.get("entry", [])[0]
    changes = entry.get("changes", [])[0]
    value   = changes.get("value", {})
    messages = value.get("messages", [])

    # Sometimes 360dialog sends status updates with no “messages” array
    if not messages:
        return make_response("No messages to process", 200)

    message     = messages[0]
    from_number = message.get("from")  # e.g. "6591234567"
    msg_type    = message.get("type")

    ##############################
    # 1) Plain-Text “reset” or Flow Starters
    ##############################
    if msg_type == "text":
        text_body = message["text"]["body"].strip().lower()

        # If user typed “reset”, clear all flow states and re-show main menu
        if text_body == "reset":
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)
            car_fumigation.send_main_menu(to=from_number, phone_number_id=PHONE_NUMBER_ID)
            return make_response("Reset & main menu sent", 200)

        # “Need help on Mold!” → start mold flow
        if text_body == "need help on mold!":
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            state = {"step": "mold_intro"}
            set_user_state(REDIS_PREFIX_MOLD, from_number, state)
            mold.send_mold_option_prompt(to=from_number, phone_number_id=PHONE_NUMBER_ID)
            return make_response("Started Mold flow", 200)

        # “Need help on Pest!” → show pest control list (car/bedbug)
        if text_body in ["need help on pest!", "need help on pest"]:
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            state = {"step": "choose_service"}
            set_user_state(REDIS_PREFIX_CAR, from_number, state)
            car_fumigation.send_pest_control_list(to=from_number, phone_number_id=PHONE_NUMBER_ID)
            return make_response("Pest control list sent", 200)

    ##############################
    # 2) Button or Quick-Reply Payloads
    ##############################
    if msg_type in ["button", "interactive"]:
        # Extract payload ID for button replies
        def extract_button_payload(msg):
            if msg.get("type") == "button":
                return msg["button"]["payload"]
            if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
                return msg["interactive"]["button_reply"]["id"]
            return ""

        payload = extract_button_payload(message).strip()
        payload_lower = payload.lower()

        # ===== a) If any flow is already “in progress”, delegate to that flow’s handler =====
        # ----- Mold flow in progress? -----
        state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
        if state_mold:
            mold.handle_mold_flow(from_number=from_number, message=message, user_state=state_mold)
            return make_response("Delegated to Mold flow", 200)

        # ----- Bedbug flow in progress? -----
        state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
        if state_bed:
            bedbug.handle_bedbug_flow(from_number=from_number, message=message, user_state=state_bed)
            return make_response("Delegated to Bedbug flow", 200)

        # ----- Car Fumigation flow in progress? -----
        state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
        if state_car:
            car_fumigation.handle_car_fumigation_flow(from_number=from_number, message=message, user_state=state_car)
            return make_response("Delegated to Car Fumigation flow", 200)

        # ===== b) No flow in progress → maybe they clicked on “Need help on Mold/Pest” buttons from main menu =====
        if payload_lower == "need help on mold!":
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            state = {"step": "mold_intro"}
            set_user_state(REDIS_PREFIX_MOLD, from_number, state)
            mold.send_mold_option_prompt(to=from_number, phone_number_id=PHONE_NUMBER_ID)
            return make_response("Started Mold flow via button", 200)

        if payload_lower in ["need help on pest!", "need help on pest"]:
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            state = {"step": "choose_service"}
            set_user_state(REDIS_PREFIX_CAR, from_number, state)
            car_fumigation.send_pest_control_list(to=from_number, phone_number_id=PHONE_NUMBER_ID)
            return make_response("Started Pest flow via button", 200)

        # ===== c) Fallback: No recognized payload, resend main menu instructions =====
        send_text_message(
            to=from_number,
            body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
        )
        return make_response("Unrecognized button payload", 200)

    ##############################
    # 3) List-Reply Handling
    ##############################
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"].strip().lower()

        # ----- Car flow in progress? -----
        state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
        if state_car:
            # If currently in “choose_service” step and user picked “bedbugs”, switch to bedbug flow
            if state_car.get("step") == "choose_service" and selected_id == "bedbugs":
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                state = {"step": "bedbug_intro"}
                set_user_state(REDIS_PREFIX_BED, from_number, state)
                bedbug.send_bedbug_option_prompt(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return make_response("Switched to Bedbug flow", 200)
            # Otherwise let Car Fumigation handler handle it
            car_fumigation.handle_car_fumigation_flow(from_number=from_number, message=message, user_state=state_car)
            return make_response("List reply delegated to Car flow", 200)

        # ----- Mold flow in progress? -----
        state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
        if state_mold:
            mold.handle_mold_flow(from_number=from_number, message=message, user_state=state_mold)
            return make_response("List reply delegated to Mold flow", 200)

        # ----- Bedbug flow in progress? -----
        state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
        if state_bed:
            bedbug.handle_bedbug_flow(from_number=from_number, message=message, user_state=state_bed)
            return make_response("List reply delegated to Bedbug flow", 200)

        # No flow in progress → fallback
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t expect that. Type 'reset' to start over."
        )
        return make_response("Unrecognized list reply", 200)

    ##############################
    # 4) Any other message type (image, video, etc.)
    ##############################
    # Send an “echo” template that tells the user we didn’t understand
    send_template_message(
        to=from_number,
        template_name=ECHO_TEMPLATE,
        template_params=[from_number]  # or any placeholder your template expects
    )
    return make_response("Echo template sent", 200)


if __name__ == "__main__":
    # For local testing
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
