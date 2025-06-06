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
from flows import bedbug  # Import the bedbug flow

app = Flask(__name__)

VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Prefixes for Redis keys (used by your helper functions)
REDIS_PREFIX_CAR  = "carfum"
REDIS_PREFIX_MOLD = "mold"
REDIS_PREFIX_BED  = "bedbug"

# Name of your main menu template (must be defined in 1MSG Dashboard),
# and it expects exactly ONE body parameter ({{1}}).
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    When you configure the webhook URL in 1MSG, they send a GET request:
      /webhook?hub.verify_token=<VERIFY_TOKEN>&hub.challenge=<challenge>
    We must echo back the 'hub.challenge' if the token matches.
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
    Main webhook to receive incoming messages from 1MSG.
    1MSG’s POST body structure:
      {
        "messages": [
          {
            "chatId": "6589123456@c.us",
            "type": "chat" | "button" | "interactive",
            "body": "hello",                      # only if type == "chat" or type == "button"
            "button_reply": {"id":"quick_reply_1"},  # if type == "button"
            "interactive": {
               "type": "list_reply" or "button_reply",
               ...
            },
            ...
          }
        ],
        "instanceId": "VAN388218473"
      }
    """
    payload = request.get_json()
    print(f"[DEBUG] Received raw message payload: {json.dumps(payload)}")

    # 1) Extract the "messages" array instead of entry/changes/value/messages
    messages = payload.get("messages", [])
    if not messages:
        return make_response("No messages to process", 200)

    message = messages[0]
    from_number = message.get("chatId")
    msg_type    = message.get("type")
    print(f"[DEBUG] from={from_number}, type={msg_type}, message={json.dumps(message)}")

    # ——————————————————————————————————————————————
    # A) Handle plain-text ("chat") messages
    # ——————————————————————————————————————————————
    if msg_type == "chat":
        text_body = message.get("body", "").strip().lower()
        print(f"[DEBUG] Received TEXT from {from_number}: '{text_body}'")

        # ——— “reset” command: clear all states + send main menu ———
        if text_body == "reset":
            print(f"[DEBUG] 'reset' detected for {from_number}. Clearing all states and sending main menu.")
            clear_user_state(REDIS_PREFIX_CAR, from_number)
            clear_user_state(REDIS_PREFIX_MOLD, from_number)
            clear_user_state(REDIS_PREFIX_BED, from_number)

            # SEND the main menu template with EXACTLY ONE placeholder string.
            # If you want a blank placeholder, just send "".
            send_template_message(
                to=from_number,
                template_name=MAIN_MENU_TEMPLATE,
                template_params=[""]   # ← exactly one element
            )
            return make_response("Reset: Main menu sent", 200)

        # ——— “Need help on Mold!” → start Mold flow ———
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

        # ——— “Need help on Pest!” → start Car (Pest) flow ———
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

        # ——— If user is already in a Mold flow, delegate TEXT to it ———
        state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
        if state_mold:
            print(f"[DEBUG] Delegating TEXT to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
            mold.handle_mold_flow(
                from_number=from_number,
                message=message,
                user_state=state_mold
            )
            return make_response("Mold flow TEXT handled", 200)

        # ——— If user is already in a Bedbug flow, delegate TEXT to it ———
        state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
        if state_bed:
            print(f"[DEBUG] Delegating TEXT to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
            bedbug.handle_bedbug_flow(
                from_number=from_number,
                message=message,
                user_state=state_bed
            )
            return make_response("Bedbug flow TEXT handled", 200)

        # ——— If user is already in a Car (Pest) flow, delegate TEXT to it ———
        state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
        if state_car:
            print(f"[DEBUG] Delegating TEXT to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
            car_fumigation.handle_car_fumigation_flow(
                from_number=from_number,
                message=message,
                user_state=state_car
            )
            return make_response("Car flow TEXT handled", 200)

        # ——— No active flow & unrecognized text → send fallback prompt ———
        send_text_message(
            to=from_number,
            body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
        )
        return make_response("No active flow & TEXT fallback sent", 200)

    # ——————————————————————————————————————————————
    # B) Handle quick-reply BUTTON or interactive BUTTON_REPLY
    # ——————————————————————————————————————————————
    if msg_type in ["button", "interactive"]:
        def extract_button_payload(msg: dict) -> str:
            """
            1MSG “button” → top-level "body"
            1MSG interactive with type=="button_reply" → msg["interactive"]["button_reply"]["id"]
            """
            msg_type_inner = msg.get("type", "")
            # If it’s a 1MSG quick-reply, type == "button", text is in msg["body"]
            if msg_type_inner == "button":
                return msg.get("body", "").strip()

            # If interactive type == "button_reply"
            if (msg_type_inner == "interactive"
                    and msg.get("interactive", {}).get("type") == "button_reply"):
                return msg["interactive"]["button_reply"].get("id", "").strip()

            return ""

        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] Received BUTTON payload='{payload_lower}' from {from_number}")

            # ——— Main-menu button “Need help on Mold!” ———
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

            # ——— Main-menu button “Need help on Pest!” ———
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

            # ——— If in Mold flow already, delegate BUTTON to it ———
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                print(f"[DEBUG] Delegating BUTTON to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow BUTTON handled", 200)

            # ——— If in Bedbug flow already, delegate BUTTON to it ———
            state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
            if state_bed:
                print(f"[DEBUG] Delegating BUTTON to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
                bedbug.handle_bedbug_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_bed
                )
                return make_response("Bedbug flow BUTTON handled", 200)

            # ——— If in Car (Pest) flow already, delegate BUTTON to it ———
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                print(f"[DEBUG] Delegating BUTTON to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow BUTTON handled", 200)

            # ——— No active flow & unknown BUTTON → fallback text ———
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No active flow for BUTTON, fallback sent", 200)

    # ——————————————————————————————————————————————
    # C) Handle interactive LIST replies
    # ——————————————————————————————————————————————
    if msg_type == "interactive" and message.get("interactive", {}).get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] Received LIST reply '{selected_id}' from {from_number}")

        # 1) If in Bedbug flow, delegate LIST to it
        state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
        if state_bed:
            print(f"[DEBUG] Delegating LIST to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
            bedbug.handle_bedbug_flow(
                from_number=from_number,
                message=message,
                user_state=state_bed
            )
            return make_response("Bedbug flow LIST handled", 200)

        # 2) If in Car (Pest) flow, check if they chose “bedbugs” under choose_service
        state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
        if state_car:
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

            # Otherwise, delegate LIST to Car (Pest) flow
            print(f"[DEBUG] Delegating LIST to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
            car_fumigation.handle_car_fumigation_flow(
                from_number=from_number,
                message=message,
                user_state=state_car
            )
            return make_response("Car flow LIST handled", 200)

        # 3) If in Mold flow, delegate LIST to it
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

    # ——————————————————————————————————————————————
    # D) Fallback for any other msg_type
    # ——————————————————————————————————————————————
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
