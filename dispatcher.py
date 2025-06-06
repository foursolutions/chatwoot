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
from flows import bedbug  # Import your bedbug flow here

app = Flask(__name__)

VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Redis‐key prefixes for each flow
REDIS_PREFIX_CAR  = "carfum"
REDIS_PREFIX_MOLD = "mold"
REDIS_PREFIX_BED  = "bedbug"

# Name of the main‐menu template (1MSG Dashboard) which expects exactly ONE placeholder {{1}}
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")
MAIN_MENU_GREETING = (
    "Hi there, thanks for reaching out to Four Solutions! How may I help you today?"
)


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    1MSG’s GET verification request looks like:
      /webhook?hub.verify_token=<VERIFY_TOKEN>&hub.challenge=<challenge>
    We must return the challenge if the token matches.
    """
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return make_response(challenge, 200)
    else:
        return make_response("Verification token mismatch", 403)


@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Main webhook for 1MSG. 1MSG POST body has:
      {
        "messages": [
          {
            "chatId": "6589123456@c.us",
            "fromMe": false,         # true if the message was sent by us
            "type": "chat" | "button" | "interactive",
            "body": "reset",         # for type=="chat"
            "button_reply": {"id": "...", "title": "..."},  # for type=="button"
            "list_reply": {"id": "...", "title": "...", "description": "..."},  # for type=="interactive" (list)
            … and other fields …
          }
        ],
        "instanceId": "VAN…"
      }
    """
    payload = request.get_json()
    print(f"[DEBUG] Received raw message payload: {json.dumps(payload)}")

    messages = payload.get("messages", [])
    if not messages:
        # Nothing to do if there is no “messages” array or it’s empty
        return make_response("No messages to process", 200)

    message = messages[0]
    from_number = message.get("chatId")
    msg_type    = message.get("type")
    print(f"[DEBUG] from={from_number}, type={msg_type}, message={json.dumps(message)}")

    # ────────────────────────────────────────────────────
    # 1) IGNORE any message that the bot itself sent (fromMe=true)
    # ────────────────────────────────────────────────────
    # 1MSG echoes back every outgoing message with "fromMe": true. If we process that,
    # we’ll loop. So we must bail out immediately.
    if message.get("fromMe", False):
        print(f"[DEBUG] Ignoring message fromMe=true (bot’s own message).")
        return make_response("Ignored bot’s own message", 200)

    # ────────────────────────────────────────────────────
    # A) Handle “chat” (plain‐text) messages
    # ────────────────────────────────────────────────────
    if msg_type == "chat":
        text_body = message.get("body", "").strip().lower()
        print(f"[DEBUG] Received TEXT from {from_number}: '{text_body}'")

        # —— “reset” command: clear all flows + send main menu —— 
        if text_body == "reset":
            print(f"[DEBUG] 'reset' detected for {from_number}. Clearing states and sending main menu.")
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)

            send_template_message(
                to=from_number,
                template_name=MAIN_MENU_TEMPLATE,
                template_params=[MAIN_MENU_GREETING]
            )
            return make_response("Reset: Main menu sent", 200)

        # —— “Need help on Mold!” → start Mold flow —— 
        if text_body in ["need help on mold!", "need help on mold"]:
            print(f"[DEBUG] 'need help on mold!' detected for {from_number}. Starting mold flow.")
            clear_user_state(REDIS_PREFIX_MOLD, from_number)

            new_state = {"step": "mold_option", "affected_areas": []}
            set_user_state(REDIS_PREFIX_MOLD, from_number, new_state)

            mold.send_mold_option_prompt(
                to=from_number,
                phone_number_id=PHONE_NUMBER_ID
            )
            return make_response("Mold flow started", 200)

        # —— “Need help on Pest!” → start Car/Pest flow —— 
        if text_body in ["need help on pest!", "need help on pest"]:
            print(f"[DEBUG] 'need help on pest!' detected for {from_number}. Starting pest flow.")
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)

            new_state = {"step": "choose_service"}
            set_user_state(REDIS_PREFIX_CAR, from_number, new_state)

            car_fumigation.send_pest_control_list(
                to=from_number,
                phone_number_id=PHONE_NUMBER_ID
            )
            return make_response("Pest flow started", 200)

        # —— If already in a Mold flow, delegate TEXT to mold.handle_mold_flow() —— 
        state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
        if state_mold:
            print(f"[DEBUG] Delegating TEXT to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
            mold.handle_mold_flow(
                from_number=from_number,
                message=message,
                user_state=state_mold
            )
            return make_response("Mold flow TEXT handled", 200)

        # —— If already in a Bedbug flow, delegate TEXT to bedbug.handle_bedbug_flow() —— 
        state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
        if state_bed:
            print(f"[DEBUG] Delegating TEXT to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
            bedbug.handle_bedbug_flow(
                from_number=from_number,
                message=message,
                user_state=state_bed
            )
            return make_response("Bedbug flow TEXT handled", 200)

        # —— If already in a Car/Pest flow, delegate TEXT to car_fumigation.handle_car_fumigation_flow() —— 
        state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
        if state_car:
            print(f"[DEBUG] Delegating TEXT to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
            car_fumigation.handle_car_fumigation_flow(
                from_number=from_number,
                message=message,
                user_state=state_car
            )
            return make_response("Car flow TEXT handled", 200)

        # —— No active flow & unrecognized text → send fallback prompt —— 
        send_text_message(
            to=from_number,
            body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
        )
        return make_response("No active flow & TEXT fallback sent", 200)

    # ────────────────────────────────────────────────────
    # B) Handle quick‐reply “button” or interactive “button_reply”
    # ────────────────────────────────────────────────────
    if msg_type in ["button", "interactive"]:
        def extract_button_payload(msg: dict) -> str:
            """
            1) If it’s a 1MSG quick‐reply button, then type=="button" and the chosen ID/text is in msg["body"].  
            2) If it’s a template button under interactive, then type=="interactive" and you look at msg["button_reply"]["id"].
            """
            msg_type_inner = msg.get("type", "")
            # Case 1: a 1MSG “button” quick‐reply → payload is msg["body"]
            if msg_type_inner == "button":
                return msg.get("body", "").strip()

            # Case 2: an interactive template‐button → it shows up under interactive.button_reply
            if (
                msg_type_inner == "interactive"
                and msg.get("button_reply", {}) is not None
            ):
                return msg["button_reply"].get("id", "").strip()

            return ""

        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] Received BUTTON payload='{payload_lower}' from {from_number}")

            # —— Main‐menu button “Need help on Mold!” —— 
            if payload_lower in ["need help on mold!", "need help on mold"]:
                print(f"[DEBUG] 'need help on mold!' detected via BUTTON for {from_number}.")
                clear_user_state(REDIS_PREFIX_MOLD, from_number)

                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(REDIS_PREFIX_MOLD, from_number, new_state)

                mold.send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Mold flow started via BUTTON", 200)

            # —— Main‐menu button “Need help on Pest!” —— 
            if payload_lower in ["need help on pest!", "need help on pest"]:
                print(f"[DEBUG] 'need help on pest!' detected via BUTTON for {from_number}.")
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_BED, from_number)

                new_state = {"step": "choose_service"}
                set_user_state(REDIS_PREFIX_CAR, from_number, new_state)

                car_fumigation.send_pest_control_list(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Pest flow started via BUTTON", 200)

            # —— If already in Mold flow, delegate BUTTON to mold.handle_mold_flow() —— 
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                print(f"[DEBUG] Delegating BUTTON to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow BUTTON handled", 200)

            # —— If already in Bedbug flow, delegate BUTTON to bedbug.handle_bedbug_flow() —— 
            state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
            if state_bed:
                print(f"[DEBUG] Delegating BUTTON to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
                bedbug.handle_bedbug_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_bed
                )
                return make_response("Bedbug flow BUTTON handled", 200)

            # —— If already in Car/Pest flow, delegate BUTTON to car_fumigation.handle_car_fumigation_flow() —— 
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                print(f"[DEBUG] Delegating BUTTON to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow BUTTON handled", 200)

            # —— No active flow & unknown BUTTON → fallback text —— 
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No active flow for BUTTON, fallback sent", 200)

    # ────────────────────────────────────────────────────
    # C) Handle “interactive list_reply”
    # ────────────────────────────────────────────────────
    # In 1MSG, when the user taps a list item, the JSON has:
    #     "type": "interactive"
    #     "list_reply": { "id": "...", "title": "...", "description": "..." }
    # So we look for msg_type=="interactive" AND message.get("list_reply") exists.
    if msg_type == "interactive" and message.get("list_reply") is not None:
        selected_id = message["list_reply"].get("id", "")
        print(f"[DEBUG] Received LIST reply '{selected_id}' from {from_number}")

        # 1) If in Bedbug flow already, delegate LIST to bedbug.handle_bedbug_flow()
        state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
        if state_bed:
            print(f"[DEBUG] Delegating LIST to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
            bedbug.handle_bedbug_flow(
                from_number=from_number,
                message=message,
                user_state=state_bed
            )
            return make_response("Bedbug flow LIST handled", 200)

        # 2) If in Car/Pest flow, check if they chose “bedbugs” under choose_service
        state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
        if state_car:
            # If step == "choose_service" and they tapped "bedbugs", switch to bedbug flow
            if state_car.get("step") == "choose_service" and selected_id == "bedbugs":
                print(f"[DEBUG] User chose bedbugs under pest services. Starting Bedbug flow.")
                clear_user_state(REDIS_PREFIX_CAR, from_number)

                new_state = {"step": "bedbug_option", "affected_areas": []}
                set_user_state(REDIS_PREFIX_BED, from_number, new_state)

                bedbug.send_bedbug_option_prompt(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Started Bedbug flow via LIST choice", 200)

            # Otherwise, delegate LIST to Car/Pest flow
            print(f"[DEBUG] Delegating LIST to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
            car_fumigation.handle_car_fumigation_flow(
                from_number=from_number,
                message=message,
                user_state=state_car
            )
            return make_response("Car flow LIST handled", 200)

        # 3) If in Mold flow, delegate LIST to mold.handle_mold_flow()
        state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
        if state_mold:
            print(f"[DEBUG] Delegating LIST to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
            mold.handle_mold_flow(
                from_number=from_number,
                message=message,
                user_state=state_mold
            )
            return make_response("Mold flow LIST handled", 200)

        # 4) No active flow & unknown LIST → fallback text
        send_text_message(
            to=from_number,
            body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
        )
        return make_response("No flow active for LIST, fallback sent", 200)

    # ────────────────────────────────────────────────────
    # D) Fallback for any other msg_type
    # ────────────────────────────────────────────────────
    print(f"[DEBUG] Received unsupported msg_type='{msg_type}' from {from_number}. Sending fallback.")
    send_text_message(
        to=from_number,
        body=(
            "Sorry, I can’t handle that type of message.  \n"
            "Please tap 'Need help on Pest!' or 'Need help on Mold!' or type 'reset'."
        )
    )
    return make_response("Unsupported message type fallback sent", 200)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
