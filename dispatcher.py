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
from flows import bedbug
from flows import mold

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def receive_message():
    # ─────── Handle verification (GET) ────────────────────────────────────────
    if request.method == "GET":
        verify_token = os.getenv("VERIFY_TOKEN")
        mode         = request.args.get("hub.mode")
        token        = request.args.get("hub.verify_token")
        challenge    = request.args.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            return make_response(challenge, 200)
        return make_response("Verification token mismatch", 403)

    # ─────── Handle incoming message (POST) ───────────────────────────────────
    payload = request.get_json()
    try:
        # ─── Check if this is a 1msg-wrapped payload ───────────────────────────
        #
        # When 1msg sits in front of 360dialog, inbound JSON looks like:
        # {
        #   "data": {
        #     "payload": {
        #       "360dialog": {
        #         "messages": [
        #           {
        #             "from": "659XXXXXXXX",
        #             "type": "text",
        #             "text": { "body": "hello bot" }
        #           }
        #         ]
        #       }
        #     }
        #   }
        # }
        #
        # So if payload["data"]["payload"]["360dialog"]["messages"] exists, unwrap it now.
        if (
            isinstance(payload, dict)
            and payload.get("data")
            and isinstance(payload["data"], dict)
            and payload["data"].get("payload")
            and isinstance(payload["data"]["payload"], dict)
            and payload["data"]["payload"].get("360dialog")
        ):
            # This is a 1msg-forwarded object. Grab the real 'messages' array:
            raw360   = payload["data"]["payload"]["360dialog"]
            messages = raw360.get("messages", [])

        else:
            # Fallback to the original "entry → changes → value → messages" logic
            entry    = payload.get("entry", [])[0]
            changes  = entry.get("changes", [])[0]
            value    = changes.get("value", {})
            messages = value.get("messages", [])

        # ─── If there are no messages to process, return 200 ────────────────────
        if not messages:
            return make_response("No messages to process", 200)

        # Now 'messages' is either from 1msg or from direct Graph-API style
        message     = messages[0]
        from_number = message["from"]
        msg_type    = message.get("type")

        # ─── Route by message type ──────────────────────────────────────────────
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()

            # If user sends "reset", clear any stored state
            if text_body == "reset":
                clear_user_state("car", from_number)
                clear_user_state("bedbug", from_number)
                clear_user_state("mold", from_number)
                send_text_message(
                    to=from_number,
                    body="Your session has been reset. How can I help you today? "
                         "Please type 'Need help on Pest!', 'Need help on Mold!', "
                         "or 'Need help on Car!'",
                )
                return make_response("User session reset", 200)

            # If user types "Need help on Car!", start the car fumigation flow
            if "need help on car" in text_body:
                clear_user_state("bedbug", from_number)
                clear_user_state("mold", from_number)
                send_template_message(
                    to=from_number,
                    template_name="Car_Main_Menu",
                    template_params=[]
                )
                return make_response("Car fumigation menu sent", 200)

            # If user types "Need help on Pest!" start the pest flow (bedbug)
            if "need help on pest" in text_body:
                clear_user_state("car", from_number)
                clear_user_state("mold", from_number)
                send_template_message(
                    to=from_number,
                    template_name="Bedbug_Main_Menu",
                    template_params=[]
                )
                return make_response("Bedbug menu sent", 200)

            # If user types "Need help on Mold!" start the mold flow
            if "need help on mold" in text_body:
                clear_user_state("car", from_number)
                clear_user_state("bedbug", from_number)
                send_template_message(
                    to=from_number,
                    template_name="Mold_Main_Menu",
                    template_params=[]
                )
                return make_response("Mold menu sent", 200)

            # Otherwise delegate to whichever flow has an active state
            car_state    = get_user_state("car", from_number)
            bedbug_state = get_user_state("bedbug", from_number)
            mold_state   = get_user_state("mold", from_number)

            if car_state:
                return car_fumigation.handle(from_number, message, car_state)
            elif bedbug_state:
                return bedbug.handle(from_number, message, bedbug_state)
            elif mold_state:
                return mold.handle(from_number, message, mold_state)
            else:
                # No active state, unrecognized text
                send_template_message(
                    to=from_number,
                    template_name="Fallback_Unrecognized",
                    template_params=[
                        "Sorry, I can’t handle that type of message. "
                        "Please tap 'Need help on Pest!' or 'Need help on Mold!' or type 'reset'."
                    ]
                )
                return make_response("Unsupported text fallback sent", 200)

        elif msg_type == "interactive":
            # For interactive replies (buttons, list selections), extract user response
            interactive = message.get("interactive", {})
            i_type      = interactive.get("type")

            # Quick reply or button
            if i_type == "button_reply":
                button_id   = interactive["button_reply"]["id"]
                button_text = interactive["button_reply"]["title"].strip().lower()

                # Delegate based on active state
                car_state    = get_user_state("car", from_number)
                bedbug_state = get_user_state("bedbug", from_number)
                mold_state   = get_user_state("mold", from_number)

                if car_state:
                    return car_fumigation.handle(from_number, message, car_state)
                elif bedbug_state:
                    return bedbug.handle(from_number, message, bedbug_state)
                elif mold_state:
                    return mold.handle(from_number, message, mold_state)
                else:
                    # No active state: show the main menu again
                    send_template_message(
                        to=from_number,
                        template_name="Main_Menu",
                        template_params=[]
                    )
                    return make_response("No active flow, main menu re-sent", 200)

            # List reply
            elif i_type == "list_reply":
                list_id    = interactive["list_reply"]["id"]
                list_text  = interactive["list_reply"]["title"].strip().lower()

                # Delegate based on active state
                car_state    = get_user_state("car", from_number)
                bedbug_state = get_user_state("bedbug", from_number)
                mold_state   = get_user_state("mold", from_number)

                if car_state:
                    return car_fumigation.handle(from_number, message, car_state)
                elif bedbug_state:
                    return bedbug.handle(from_number, message, bedbug_state)
                elif mold_state:
                    return mold.handle(from_number, message, mold_state)
                else:
                    # No active state: show the main menu again
                    send_template_message(
                        to=from_number,
                        template_name="Main_Menu",
                        template_params=[]
                    )
                    return make_response("No active flow, main menu re-sent", 200)

            else:
                # Unhandled interactive type
                send_text_message(
                    to=from_number,
                    body="Sorry, I didn’t understand your selection. Please try again or type 'reset' to start over."
                )
                return make_response("Unhandled interactive type", 200)

        else:
            # Any other message type (e.g., image, video, stickers, etc.)
            send_template_message(
                to=from_number,
                template_name="Fallback_Unhandled_Type",
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
