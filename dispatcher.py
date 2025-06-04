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

VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


@app.route("/webhook", methods=["GET", "POST"])
def receive_message():
    # ─────── Handle verification (GET) ────────────────────────────────────────
    if request.method == "GET":
        mode      = request.args.get("hub.mode")
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return make_response(challenge, 200)
        return make_response("Verification token mismatch", 403)

    # ─────── Handle incoming message (POST) ───────────────────────────────────
    payload = request.get_json()

    # ─────── Debug: log the raw JSON so we can inspect it ────────────────────
    try:
        print(">>>> RAW INCOMING JSON:", json.dumps(payload))
    except Exception:
        print(">>>> RAW INCOMING PAYLOAD (non‐JSON‐serializable):", str(payload))

    try:
        messages = None

        # 1) Check for 1msg “WhatsApp Web” wrapper (has top-level "messages" list)
        if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
            messages = payload["messages"]

        # 2) If not found, check for 1msg “360dialog” wrapper:
        #    payload["data"]["payload"]["360dialog"]["messages"]
        if messages is None:
            data_section = payload.get("data")
            if isinstance(data_section, dict):
                inner = data_section.get("payload")
                if isinstance(inner, dict):
                    wrapped360 = inner.get("360dialog")
                    if isinstance(wrapped360, dict):
                        messages = wrapped360.get("messages", [])

        # 3) If still no messages, fallback to original Facebook Graph format:
        #    payload["entry"][0]["changes"][0]["value"]["messages"]
        if messages is None or not isinstance(messages, list) or len(messages) == 0:
            entry_list = payload.get("entry")
            if isinstance(entry_list, list) and len(entry_list) > 0:
                first_entry = entry_list[0]
                changes_list = first_entry.get("changes")
                if isinstance(changes_list, list) and len(changes_list) > 0:
                    first_change = changes_list[0]
                    value_section = first_change.get("value", {})
                    messages = value_section.get("messages", [])

        # If still no messages, do nothing
        if not isinstance(messages, list) or len(messages) == 0:
            return make_response("No messages to process", 200)

        # We now have messages[0] as the incoming message
        message = messages[0]

        # ─── Determine “from_number” and “msg_type” ─────────────────────────────
        # Case A: 1msg “WhatsApp Web” wrapper (“author” + “body” fields)
        if "author" in message and "body" in message:
            author_full = message.get("author", "")
            from_number = author_full.split("@")[0] if "@" in author_full else author_full
            msg_type    = "chat"
            text_body   = message.get("body", "").strip().lower()
        else:
            # Cases B & C: both “360dialog” wrapper and original Graph format use 
            # “from” + “type” + “text” fields
            from_number = message.get("from")
            msg_type    = message.get("type")
            text_body   = ""
            if msg_type == "text":
                text_body = message.get("text", {}).get("body", "").strip().lower()

        # If anything is missing, bail
        if not from_number or not msg_type:
            return make_response("Invalid message format", 200)

        # ─── ROUTING BY MESSAGE TYPE ────────────────────────────────────────────
        # We treat both “chat” (WhatsApp Web) and “text” (360dialog/Graph) as text flows.
        if msg_type in ("text", "chat"):
            # (1) If the user typed “reset”, clear all states and show MAIN MENU
            if text_body == "reset":
                clear_user_state("car",    from_number)
                clear_user_state("bedbug", from_number)
                clear_user_state("mold",   from_number)

                # CALL THE EXACT send_main_menu() YOU ALREADY HAVE IN car_fumigation.py
                # That template is “main_menu_v2” with greeting_name = "there" by default. 
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Reset → main menu sent", 200)

            # (2) If user typed “Need help on Car!”, start Car flow
            if "need help on car" in text_body:
                clear_user_state("bedbug", from_number)
                clear_user_state("mold",   from_number)
                send_template_message(
                    to=from_number,
                    template_name="car_fum_menu",
                    template_params=[]
                )
                return make_response("Car fumigation menu sent", 200)

            # (3) If user typed “Need help on Pest!”, start Bedbug flow
            if "need help on pest" in text_body:
                clear_user_state("car",   from_number)
                clear_user_state("mold",  from_number)
                send_template_message(
                    to=from_number,
                    template_name="Bedbug_Main_Menu",
                    template_params=[]
                )
                return make_response("Bedbug menu sent", 200)

            # (4) If user typed “Need help on Mold!”, start Mold flow
            if "need help on mold" in text_body:
                clear_user_state("car",    from_number)
                clear_user_state("bedbug", from_number)
                send_template_message(
                    to=from_number,
                    template_name="Mold_Main_Menu",
                    template_params=[]
                )
                return make_response("Mold menu sent", 200)

            # (5) Otherwise, delegate into whichever flow has an active state
            car_state    = get_user_state("car",    from_number)
            bedbug_state = get_user_state("bedbug", from_number)
            mold_state   = get_user_state("mold",   from_number)

            if car_state:
                return car_fumigation.handle_car_fumigation_flow(from_number, message, car_state)
            elif bedbug_state:
                return bedbug.handle(from_number, message, bedbug_state)
            elif mold_state:
                return mold.handle(from_number, message, mold_state)
            else:
                # No active flow: send a generic “I didn’t understand” template
                send_template_message(
                    to=from_number,
                    template_name="Fallback_Unrecognized",
                    template_params=[
                        (
                            "Sorry, I didn’t understand that. "
                            "You can type ‘reset’ to see the main menu again."
                        )
                    ]
                )
                return make_response("Unsupported text fallback sent", 200)

        # ─── Handle interactive messages (buttons / list replies) ─────────────────────
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            i_type      = interactive.get("type")

            # BUTTON_REPLY (user tapped a quick‐reply button)
            if i_type == "button_reply":
                button_id   = interactive["button_reply"].get("id", "")
                button_text = interactive["button_reply"].get("title", "").strip().lower()

                car_state    = get_user_state("car",    from_number)
                bedbug_state = get_user_state("bedbug", from_number)
                mold_state   = get_user_state("mold",   from_number)

                if car_state:
                    return car_fumigation.handle_car_fumigation_flow(from_number, message, car_state)
                elif bedbug_state:
                    return bedbug.handle(from_number, message, bedbug_state)
                elif mold_state:
                    return mold.handle(from_number, message, mold_state)
                else:
                    # No active flow: show the main menu again
                    car_fumigation.send_main_menu(
                        to=from_number,
                        phone_number_id=PHONE_NUMBER_ID
                    )
                    return make_response("No active flow → main menu re-sent", 200)

            # LIST_REPLY (user selected from an interactive list)
            elif i_type == "list_reply":
                list_id    = interactive["list_reply"].get("id", "")
                list_text  = interactive["list_reply"].get("title", "").strip().lower()

                car_state    = get_user_state("car",    from_number)
                bedbug_state = get_user_state("bedbug", from_number)
                mold_state   = get_user_state("mold",   from_number)

                if car_state:
                    return car_fumigation.handle_car_fumigation_flow(from_number, message, car_state)
                elif bedbug_state:
                    return bedbug.handle(from_number, message, bedbug_state)
                elif mold_state:
                    return mold.handle(from_number, message, mold_state)
                else:
                    # No active flow: re-send the main menu
                    car_fumigation.send_main_menu(
                        to=from_number,
                        phone_number_id=PHONE_NUMBER_ID
                    )
                    return make_response("No active flow → main menu re-sent", 200)

            else:
                # Unhandled interactive type
                send_text_message(
                    to=from_number,
                    body=(
                        "Sorry, I didn’t understand your selection. "
                        "Type ‘reset’ to return to the main menu."
                    )
                )
                return make_response("Unhandled interactive type", 200)

        # ─── Fallback for any other message type (image, audio, etc.) ───────────────────
        else:
            send_template_message(
                to=from_number,
                template_name="Fallback_Unhandled_Type",
                template_params=[
                    (
                        "Sorry, I can’t handle that type of message right now. "
                        "Type ‘reset’ to return to the main menu."
                    )
                ]
            )
            return make_response("Unsupported message type fallback sent", 200)

    except Exception as e:
        print(f"Error in receive_message: {e}")
        return make_response("Error processing message", 200)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
