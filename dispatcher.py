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
from flows import bedbug  # Import the new bedbug flow

app = Flask(__name__)

VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Prefixes for Redis keys
REDIS_PREFIX_CAR  = "carfum"
REDIS_PREFIX_MOLD = "mold"
REDIS_PREFIX_BED  = "bedbug"

# Main menu template name (must match your 1MSG template)
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    1MSG will send GET /webhook?hub.verify_token=<VERIFY_TOKEN>&hub.challenge=<challenge>
    We must respond with the challenge if the token matches.
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
    Main webhook to receive incoming 1MSG messages.
    The 1MSG payload looks like:
    {
      "entry": [
        {
          "changes": [
            {
              "value": {
                "messages": [
                  {
                    "from": "6589123456@c.us",
                    "type": "text" | "button" | "interactive",
                    "text": {"body": "hello"},
                    "button": {"payload": "..."},
                    "interactive": {
                       "type": "button_reply" | "list_reply",
                       "button_reply": {"id": "..."},
                       "list_reply": {"id": "...", ...}
                    },
                    ...
                  }
                ]
              }
            }
          ]
        }
      ]
    }
    """
    payload = request.get_json()
    try:
        entry    = payload.get("entry", [])[0]
        changes  = entry.get("changes", [])[0]
        value    = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return make_response("No messages to process", 200)

        message     = messages[0]
        from_number = message["from"]
        msg_type    = message.get("type")

        # ─── 1) Plain TEXT messages ─────────────────────────────────────────────
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()
            print(f"[DEBUG] Received TEXT from {from_number}: '{text_body}'")

            # “reset” → clear all flows, re‐send main menu template
            if text_body == "reset":
                print(f"[DEBUG] 'reset' detected for {from_number}. Clearing all states and sending main menu.")
                clear_user_state(REDIS_PREFIX_CAR,  from_number)
                clear_user_state(REDIS_PREFIX_MOLD, from_number)
                clear_user_state(REDIS_PREFIX_BED,  from_number)

                # Send the main menu template
                send_template_message(
                    to=from_number,
                    template_name=MAIN_MENU_TEMPLATE,
                    template_params=[""]
                )
                return make_response("Reset: Main menu sent", 200)

            # “Need help on Mold!” → start Mold flow
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

            # “Need help on Pest!” → start Car (Pest) flow
            if text_body in ["need help on pest!", "need help on pest"]:
                print(f"[DEBUG] 'need help on pest!' detected for {from_number}. Starting pest flow.")
                # Clear any previous Car or Bedbug states
                clear_user_state(REDIS_PREFIX_CAR, from_number)
                clear_user_state(REDIS_PREFIX_BED, from_number)

                # 1) Mark CURRENT_FLOW = CAR
                new_state = {"step": "choose_service"}
                set_user_state(REDIS_PREFIX_CAR, from_number, new_state)

                # 2) Send the Pest Control Services list
                car_fumigation.send_pest_control_list(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Pest flow started", 200)

            # If none of the above TEXT commands match, check if we’re already in a flow:
            # a) Mold flow
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                print(f"[DEBUG] Delegating TEXT to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow TEXT handled", 200)

            # b) Bedbug flow
            state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
            if state_bed:
                print(f"[DEBUG] Delegating TEXT to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
                bedbug.handle_bedbug_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_bed
                )
                return make_response("Bedbug flow TEXT handled", 200)

            # c) Car (Pest) flow
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                print(f"[DEBUG] Delegating TEXT to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow TEXT handled", 200)

            # d) No flow active → fallback
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No active flow & TEXT fallback sent", 200)



        # ─── 2) BUTTONS / QUICK‐REPLY payloads ────────────────────────────────────
        if msg_type in ["button", "interactive"]:
            # Extract a BUTTON payload (1MSG “button” or interactive.button_reply)
            def extract_button_payload(msg: dict) -> str:
                # 1MSG “button” → top‐level "body"
                if msg.get("type") == "button":
                    return msg.get("body", "").strip()
                # 1MSG interactive.button_reply → nested msg["interactive"]["button_reply"]["id"]
                if (msg.get("type") == "interactive"
                        and msg["interactive"].get("type") == "button_reply"):
                    return msg["interactive"]["button_reply"].get("id", "").strip()
                return ""

            payload = extract_button_payload(message)
            if payload:
                payload_lower = payload.lower()
                print(f"[DEBUG] Received BUTTON payload='{payload_lower}' from {from_number}")

                # *** Main‐menu buttons: “Need help on Mold!” and “Need help on Pest!” ***
                if payload_lower == "need help on mold!":
                    print(f"[DEBUG] 'need help on mold!' detected via BUTTON for {from_number}.")
                    clear_user_state(REDIS_PREFIX_MOLD, from_number)

                    new_state = {"step": "mold_option", "affected_areas": []}
                    set_user_state(REDIS_PREFIX_MOLD, from_number, new_state)

                    mold.send_mold_option_prompt(
                        to=from_number,
                        phone_number_id=PHONE_NUMBER_ID
                    )
                    return make_response("Mold flow started via BUTTON", 200)

                if payload_lower == "need help on pest!":
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

                # If a flow is already active, delegate the BUTTON payload to that flow
                state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
                if state_mold:
                    print(f"[DEBUG] Delegating BUTTON to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
                    mold.handle_mold_flow(
                        from_number=from_number,
                        message=message,
                        user_state=state_mold
                    )
                    return make_response("Mold flow BUTTON handled", 200)

                state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
                if state_bed:
                    print(f"[DEBUG] Delegating BUTTON to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
                    bedbug.handle_bedbug_flow(
                        from_number=from_number,
                        message=message,
                        user_state=state_bed
                    )
                    return make_response("Bedbug flow BUTTON handled", 200)

                state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
                if state_car:
                    print(f"[DEBUG] Delegating BUTTON to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
                    car_fumigation.handle_car_fumigation_flow(
                        from_number=from_number,
                        message=message,
                        user_state=state_car
                    )
                    return make_response("Car flow BUTTON handled", 200)

                # No flow active but some other button was pressed
                send_text_message(
                    to=from_number,
                    body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
                )
                return make_response("No active flow for BUTTON, fallback sent", 200)


        # ─── 3) LIST‐REPLY (“interactive.list_reply”) payloads ─────────────────────
        if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
            selected_id = message["interactive"]["list_reply"]["id"]
            print(f"[DEBUG] Received LIST reply '{selected_id}' from {from_number}")

            # 1) If user is in Bedbug flow, delegate
            state_bed = get_user_state(REDIS_PREFIX_BED, from_number)
            if state_bed:
                print(f"[DEBUG] Delegating LIST to handle_bedbug_flow for {from_number}, step={state_bed.get('step')}")
                bedbug.handle_bedbug_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_bed
                )
                return make_response("Bedbug flow LIST handled", 200)

            # 2) If user is in Car (Pest) flow, but also check if they tapped “bedbugs” under choose_service
            state_car = get_user_state(REDIS_PREFIX_CAR, from_number)
            if state_car:
                # If step == "choose_service" and selected_id == "bedbugs", switch to Bedbug
                if state_car.get("step") == "choose_service" and selected_id == "bedbugs":
                    print(f"[DEBUG] User chose bedbugs under pest services. Clearing Car flow and starting Bedbug flow.")
                    clear_user_state(REDIS_PREFIX_CAR, from_number)

                    # Initialize Bedbug state and send first bedbug prompt
                    new_state = {"step": "bedbug_option", "affected_areas": []}
                    set_user_state(REDIS_PREFIX_BED, from_number, new_state)

                    bedbug.send_bedbug_option_prompt(
                        to=from_number,
                        phone_number_id=PHONE_NUMBER_ID
                    )
                    return make_response("Started Bedbug flow via LIST choice", 200)

                # Otherwise, delegate to Car Fumigation flow
                print(f"[DEBUG] Delegating LIST to handle_car_fumigation_flow for {from_number}, step={state_car.get('step')}")
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_car
                )
                return make_response("Car flow LIST handled", 200)

            # 3) If user is in Mold flow, delegate
            state_mold = get_user_state(REDIS_PREFIX_MOLD, from_number)
            if state_mold:
                print(f"[DEBUG] Delegating LIST to handle_mold_flow for {from_number}, step={state_mold.get('step')}")
                mold.handle_mold_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state_mold
                )
                return make_response("Mold flow LIST handled", 200)

            # 4) No active flow: send fallback
            send_text_message(
                to=from_number,
                body="Please tap 'Need help on Pest!' or 'Need help on Mold!' to begin."
            )
            return make_response("No flow active for LIST, fallback sent", 200)


        # ─── 4) Fallback for any other msg_type ───────────────────────────────────
        print(f"[DEBUG] Received unsupported msg_type='{msg_type}' from {from_number}. Sending fallback.")
        send_template_message(
            to=from_number,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=[
                "Sorry, I can’t handle that type of message. "
                "Please tap 'Need help on Pest!' or 'Need help on Mold!' or type 'reset'."
            ]
        )
        return make_response("Unsupported message type fallback sent", 200)

    except Exception as e:
        print(f"Error in receive_message: {e}")
        return make_response("Error processing message", 200)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
