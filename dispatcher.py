import os
import json
import logging
from flask import Flask, request, make_response

import helpers
import bedbug
import car_fumigation

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Redis prefixes (your existing constants)
REDIS_PREFIX_PEST = "user_state_pest:"
REDIS_PREFIX_BEDBUG = "user_state_bedbug:"
REDIS_PREFIX_CAR = "user_state_car:"
REDIS_PREFIX_MOLD = "user_state_mold:"


def extract_button_payload(msg):
    """
    This helper now returns:
      - msg["body"] for simple button replies (type=="button")
      - the .id field for interactive button_reply (type=="interactive", interactive.type=="button_reply")
      - the .id field for interactive list_reply (type=="interactive", interactive.type=="list_reply")
      - otherwise, return an empty string
    """
    # If they tapped a legacy button (1MSG button), the payload is in msg["body"]
    if msg.get("type") == "button":
        return msg.get("body", "").strip()

    # If they tapped an interactive (list or button) element in 1MSG format:
    if msg.get("type") == "interactive":
        inter = msg.get("interactive", {})
        itype = inter.get("type")

        if itype == "button_reply":
            # e.g. payload from a 1MSG button reply
            return inter.get("button_reply", {}).get("id", "").strip()

        if itype == "list_reply":
            # e.g. payload from a 1MSG list item
            return inter.get("list_reply", {}).get("id", "").strip()

    # Otherwise, no button/list payload
    return ""


def get_user_state(prefix, from_number):
    """
    Fetch user state from Redis (via your helpers.get_state).
    """
    return helpers.get_state(prefix + from_number)


def set_user_state(prefix, from_number, payload):
    """
    Save user state to Redis (via your helpers.save_state).
    """
    helpers.save_state(prefix + from_number, payload)


def clear_user_state(prefix, from_number):
    """
    Delete user state from Redis (via your helpers.clear_state).
    """
    helpers.clear_state(prefix + from_number)


@app.route("/webhook", methods=["POST"])
def receive_message():
    try:
        incoming = request.get_json(force=True)
        logging.debug(f"[DEBUG] Received raw message payload: {json.dumps(incoming)}")

        # We always grab the first message in the array
        message = incoming["messages"][0]
        from_number = message.get("senderName") or message.get("from") or message.get("author") or message.get("chatId")
        msg_type = message.get("type")
        # Extract any button or list payload (1MSG format)
        payload = extract_button_payload(message)
        payload_lower = payload.lower()

        logging.debug(f"[DEBUG] from={from_number}, type={msg_type}, payload='{payload}'")

        # 1) If it's a simple text reset, blow away all states and send main menu
        if msg_type == "chat" and message.get("body", "").strip().lower() == "reset":
            logging.debug(f"[DEBUG] 'reset' detected for {from_number}. Clearing all states and sending main menu.")
            clear_user_state(REDIS_PREFIX_PEST, from_number)
            clear_user_state(REDIS_PREFIX_BEDBUG, from_number)
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            helpers.send_main_menu(from_number)
            return make_response("Reset handled", 200)

        # 2) If the user is already in the bedbug flow, delegate (button & list replies in that flow)
        state_bed = get_user_state(REDIS_PREFIX_BEDBUG, from_number)
        if state_bed:
            logging.debug(f"[DEBUG] Delegating BUTTON to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
            bedbug.handle_bedbug_flow(
                from_number=from_number,
                message=message,
                user_state=state_bed
            )
            return make_response("Bedbug flow BUTTON handled", 200)

        # 3) If the user is already in the car fumigation flow, delegate (button & list replies in that flow)
        state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
        if state_car:
            logging.debug(f"[DEBUG] Delegating BUTTON to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
            car_fumigation.handle_car_fumigation_flow(
                from_number=from_number,
                message=message,
                user_state=state_car
            )
            return make_response("Car flow BUTTON handled", 200)

        # 4) If the user is already in the pest flow (and not bedbug/car/mold), delegate
        state_pest = get_user_state(REDIS_PREFIX_PEST, from_number)
        if state_pest:
            logging.debug(f"[DEBUG] Delegating BUTTON to handle_pest_flow for {from_number}, step={state_pest.get('step')}")
            helpers.handle_pest_flow(
                from_number=from_number,
                message=message,
                user_state=state_pest
            )
            return make_response("Pest flow BUTTON handled", 200)

        # 5) If the user is already in the mold flow, delegate
        state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
        if state_mold:
            logging.debug(f"[DEBUG] Delegating BUTTON to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
            helpers.handle_mold_flow(
                from_number=from_number,
                message=message,
                user_state=state_mold
            )
            return make_response("Mold flow BUTTON handled", 200)

        # 6) Now handle top-level interactions (no existing state)

        # 6a) If they tapped "Need help on Pest!" (1MSG button), kick off the pest flow
        if msg_type == "button" and payload_lower == "need help on pest!":
            logging.debug(f"[DEBUG] 'Need help on Pest!' detected via BUTTON for {from_number}. Starting pest flow.")
            helpers.start_pest_flow(from_number)
            return make_response("Started Pest flow", 200)

        # 6b) If they tapped "Need help on Mold!" (1MSG button), kick off the mold flow
        if msg_type == "button" and payload_lower == "need help on mold!":
            logging.debug(f"[DEBUG] 'Need help on Mold!' detected via BUTTON for {from_number}. Starting mold flow.")
            helpers.start_mold_flow(from_number)
            return make_response("Started Mold flow", 200)

        # 6c) If they tapped "Live Human" (fallback for live-human-button), hand off
        if msg_type == "button" and payload_lower == "live human":
            logging.debug(f"[DEBUG] 'Live Human' detected via BUTTON for {from_number}. Sending handoff message.")
            helpers.send_live_human_handoff(from_number)
            return make_response("Live human handoff", 200)

        # 6d) If they chose from the Pest Control Services list (1MSG list reply),
        #     the payload will be something like "car_fumigation"
        if msg_type == "interactive" and message.get("interactive", {}).get("type") == "list_reply":
            selected_id = message["interactive"]["list_reply"]["id"]
            logging.debug(f"[DEBUG] Delegating LIST to correct flow for {from_number}, selected_id={selected_id}")

            # If they selected "car_fumigation" from the list
            if selected_id.lower() == "car_fumigation":
                helpers.start_car_fumigation_flow(from_number)
                return make_response("Car fumigation flow STARTED", 200)

            # (You can add other list‐options here, e.g. bedbug, rodents, etc.)
            # elif selected_id.lower() == "bedbug_control":
            #     helpers.start_bedbug_flow(from_number)
            #     return make_response("Bedbug flow STARTED", 200)

        # 6e) If they tapped a 1MSG button under Pest Control Services that isn't a top‐level,
        #     maybe they literally pressed the “Car Fumigation 🚗” button from that list view.
        #     In that case, payload will be exactly "car_fumigation".
        if msg_type == "button" and payload_lower == "car_fumigation":
            logging.debug(f"[DEBUG] 'Car Fumigation' detected via BUTTON for {from_number}. Starting car flow.")
            helpers.start_car_fumigation_flow(from_number)
            return make_response("Car fumigation flow STARTED (button)", 200)

        # 6f) If they tapped a 1MSG button for bedbug, mold, etc. not caught above, handle analogously
        #     (e.g. if payload_lower == "bedbug_control": ...)

        # 7) Finally, if we get here, we didn’t recognize the message: send fallback
        logging.debug(f"[DEBUG] Fallback reached for {from_number}. Sending fallback prompt.")
        helpers.send_unrecognized_fallback(from_number)
        return make_response("Fallback prompt sent", 200)

    except Exception as e:
        logging.debug(f"Error in receive_message: {e}")
        return make_response("Error processing message", 200)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
