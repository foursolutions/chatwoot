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
from flows import car_fumigation
from flows import mold  # << Changed: import mold.py instead of mold_remediation

app = Flask(__name__)

# ------------------------------------------------------------------------------
#  Environment variables (must be set in Heroku config vars)
# ------------------------------------------------------------------------------
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")       # Your webhook verification token
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID") # Used by send_* functions as needed

# Redis key prefixes
REDIS_PREFIX_CAR = "carfum"
REDIS_PREFIX_MOLD = "mold"

# Name of the “echo” fallback template (approved in 360dialog)
ECHO_TEMPLATE = "echo_message_text"


# ------------------------------------------------------------------------------
#  Webhook Verification (GET)
# ------------------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Webhook verification endpoint. Meta/WhatsApp will call this with:
      - hub.mode
      - hub.verify_token
      - hub.challenge
    We must echo back the “hub.challenge” if the token matches VERIFY_TOKEN.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return make_response(challenge, 200)
    else:
        return make_response("Verification token mismatch", 403)


# ------------------------------------------------------------------------------
#  Main Webhook Handler (POST)
# ------------------------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Handle incoming WhatsApp messages sent via 360dialog:
      - Text messages
      - Interactive replies (list or quick-reply button)
      - Other types (fallback)
    We delegate to either Car Fumigation or Mold Remediation logic, based on Redis state.
    """
    payload = request.get_json()

    try:
        # Drill down into the WhatsApp payload structure:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        # If there are no messages, just return 200
        if not messages:
            return make_response("No messages to process", 200)

        message = messages[0]
        from_number = message["from"]    # e.g. "6581234567"
        msg_type = message.get("type")   # "text", "interactive", "button", etc.

        # ─── 1) Plain TEXT messages ───────────────────────────────────────────────
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()
            print(f"[DEBUG] Received TEXT from {from_number}: '{text_body}'")

            # If user types "reset" → clear both mold & car state, send main menu
            if text_body == "reset":
                print(f"[DEBUG] 'reset' detected for {from_number}. Clearing both states and sending main menu.")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Reset: Main menu sent", 200)

            # If user typed "menu" or there is no existing state → send main menu
            # But first, if they typed “need help on mold!”, route them immediately
            if text_body == "need help on mold!":
                print(f"[DEBUG] 'need help on mold!' detected for {from_number}. Starting mold flow.")
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(REDIS_PREFIX_MOLD, from_number, new_state)
                mold.send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Mold flow started", 200)

            # If they typed “need help on pest!” or “need help on pest” (just in case)
            if text_body in ["need help on pest!", "need help on pest"]:
                print(f"[DEBUG] 'need help on pest!' detected for {from_number}. Starting car flow.")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                new_state = {"step": "choose_service"}
                set_user_state(REDIS_PREFIX_CAR, from_number, new_state)
                car_fumigation.send_pest_control_list(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Car flow started", 200)

            # Otherwise, check existing Redis state for either flow
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)

            # If there’s an active Mold flow, delegate to it
            if state_mold:
                print(f"[DEBUG] Delegating TEXT to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow TEXT handled", 200)

            # Else if there’s an active Car Fum flow, delegate to it
            if state_car:
                print(f"[DEBUG] Delegating TEXT to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow TEXT handled", 200)

            # If no active flow & not “menu” or “reset”, show fallback
            if text_body == "menu" or not (state_car or state_mold):
                print(f"[DEBUG] Sending main menu to {from_number} (text_body='{text_body}')")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Main menu sent", 200)

            # Fallback for unknown text
            catchall_text = (
                "Sorry, I didn’t understand that. "
                "Please tap 'Need help on Pest!' or 'Need help on Mold!' or type 'menu' to see options again."
            )
            print(f"[DEBUG] No valid flow state & unrecognized text for {from_number}: '{text_body}'. Sending fallback.")
            send_template_message(
                to=from_number,
                template_name=ECHO_TEMPLATE,
                template_params=[catchall_text]
            )
            return make_response("Echo fallback sent", 200)

        # ─── 2) Interactive LIST replies ───────────────────────────────────────────
        elif msg_type == "interactive":
            print(f"[DEBUG] Received INTERACTIVE payload from {from_number}: {json.dumps(message)}")
            # Check which flow is active. If mold state exists, route to mold:
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow INTERACTIVE handled", 200)

            # Otherwise, if car state exists, route to car
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow INTERACTIVE handled", 200)

            # If neither, fallback to main menu
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No flow active for INTERACTIVE, fallback sent", 200)

        # ─── 3) Quick-reply BUTTON payloads ─────────────────────────────────────────
        elif msg_type == "button":
            print(f"[DEBUG] Received BUTTON payload from {from_number}: {json.dumps(message)}")
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow BUTTON handled", 200)

            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow BUTTON handled", 200)

            # Otherwise, fallback
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No flow active for BUTTON, fallback sent", 200)

        # ─── 4) Any other message types (media, etc.) → fallback ───────────────────
        else:
            catchall_text = (
                "Sorry, I can’t handle that type of message. "
                "Please tap 'Need help on Pest!' or 'Need help on Mold!' or type 'menu'."
            )
            print(f"[DEBUG] Received unsupported msg_type='{msg_type}' from {from_number}. Sending fallback.")
            send_template_message(
                to=from_number,
                template_name=ECHO_TEMPLATE,
                template_params=[catchall_text]
            )
            return make_response("Unsupported message type fallback sent", 200)

    except Exception as e:
        print(f"Error in receive_message: {e}")
        return make_response("Error processing message", 200)


# ------------------------------------------------------------------------------
#  Run the Flask app
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
