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
from flows import mold
from flows import bedbug    # ← Import your new Bedbug module

app = Flask(__name__)

# ------------------------------------------------------------------------------
#  Environment variables (must be set in Heroku config vars)
# ------------------------------------------------------------------------------
VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")   # e.g. "1234567890"
WHATSAPP_TOKEN  = os.getenv("WHATSAPP_TOKEN")    # the same token used by helpers.send_*
                                                # we’ll also pass this into bedbug

# Redis key prefixes
REDIS_PREFIX_CAR  = "carfum"
REDIS_PREFIX_MOLD = "mold"

# Fallback “echo” template name (must already be approved in 360dialog)
ECHO_TEMPLATE = "echo_message_text"

# ------------------------------------------------------------------------------
#  A simple in‐memory store for Bedbug state (you can swap this for Redis if desired)
# ------------------------------------------------------------------------------
# bedbug_data structure example:
# {
#   "6581234567": {
#       "affected_areas": [...],
#       "awaiting_area_selection": True/False,
#       ... etc ...
#   },
#   ...
# }
bedbug_data = {}

# ------------------------------------------------------------------------------
#  Webhook Verification (GET)
# ------------------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
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
    Handle incoming WhatsApp messages via 360dialog:
      - Text messages
      - Interactive replies (LIST, BUTTON, QUICK‐REPLY)
      - Fallbacks for unsupported types
    We dispatch to Car‐flow, Mold‐flow, or Bedbug‐flow based on Redis state or button/list payload.
    """
    payload = request.get_json()

    try:
        entry   = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value   = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            # Nothing to do
            return make_response("No messages to process", 200)

        message     = messages[0]
        from_number = message["from"]        # e.g. "6581234567"
        msg_type    = message.get("type")     # "text", "interactive", "button", etc.

        # ─── 1) Plain TEXT messages ─────────────────────────────────────────────
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()
            print(f"[DEBUG] Received TEXT from {from_number}: '{text_body}'")

            # If user types “reset” → clear both Car & Mold states and send main menu
            if text_body == "reset":
                print(f"[DEBUG] 'reset' detected for {from_number}. Clearing both states and sending main menu.")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Reset: Main menu sent", 200)

            # If user typed “need help on mold!”, start Mold flow immediately
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

            # If user typed “need help on pest!”, start Car flow (Pest) immediately
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

            # Otherwise, check if there is an active Mold or Car flow in Redis
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            state_car  = get_user_state(REDIS_PREFIX_CAR, from_number)

            # If active Mold flow → delegate
            if state_mold:
                print(f"[DEBUG] Delegating TEXT to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow TEXT handled", 200)

            # If active Car flow → delegate
            if state_car:
                print(f"[DEBUG] Delegating TEXT to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow TEXT handled", 200)

            # If no active flow and they typed “menu”, or unknown text → show main menu
            if text_body == "menu" or not (state_car or state_mold):
                print(f"[DEBUG] Sending main menu to {from_number} (text_body='{text_body}')")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Main menu sent", 200)

            # Fallback if we didn’t match anything
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

        # ─── 2) Interactive LIST replies ───────────────────────────────────────
        elif msg_type == "interactive":
            # An interactive payload could be LIST‐reply or BUTTON‐reply
            print(f"[DEBUG] Received INTERACTIVE payload from {from_number}: {json.dumps(message)}")

            # Check if there is an active Mold flow
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow INTERACTIVE handled", 200)

            # Otherwise, if active Car flow, delegate there
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow INTERACTIVE handled", 200)

            # Otherwise, no flow active → fallback prompt
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No flow active for INTERACTIVE, fallback sent", 200)

        # ─── 3) Quick‐reply BUTTON payloads ─────────────────────────────────────
        elif msg_type == "button":
            print(f"[DEBUG] Received BUTTON payload from {from_number}: {json.dumps(message)}")

            # Extract the button payload (the “id” we set in the interactive JSON)
            button_id = message["button"].get("payload", "")
            payload_lower = button_id.lower()

            # 1) If they tapped “Need help on Mold!”, start Mold flow
            if payload_lower == "need help on mold!":
                print(f"[DEBUG] 'Need help on Mold!' BUTTON detected for {from_number}. Starting mold flow.")
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(REDIS_PREFIX_MOLD, from_number, new_state)
                mold.send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Mold flow started via BUTTON", 200)

            # 2) If they tapped “Need help on Pest!”, start Car flow
            if payload_lower in ["need help on pest!", "need help on pest"]:
                print(f"[DEBUG] 'Need help on Pest!' BUTTON detected for {from_number}. Starting car flow.")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                new_state = {"step": "choose_service"}
                set_user_state(REDIS_PREFIX_CAR, from_number, new_state)
                car_fumigation.send_pest_control_list(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Car flow started via BUTTON", 200)

            # 3) If active Mold flow → delegate
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow BUTTON handled", 200)

            # 4) If active Car flow → delegate
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow BUTTON handled", 200)

            # 5) Otherwise, fallback
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No flow active for BUTTON, fallback sent", 200)

        # ─── 4) All other message types → fallback ───────────────────────────
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
        print(f"[ERROR] in receive_message: {e}")
        return make_response("Error processing message", 200)


# ------------------------------------------------------------------------------
#  Run the Flask app
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
