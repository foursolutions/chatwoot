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

    # ─────── Immediate debug: log the entire incoming JSON so we can inspect it ─────
    try:
        print(">>>> RAW INCOMING JSON:", json.dumps(payload))
    except Exception:
        print(">>>> RAW INCOMING PAYLOAD (non‐JSON‐serializable):", str(payload))

    try:
        messages = None

        # ─── 1) Check if payload is the 1msg‐“WhatsApp Web” wrapper ────────────────
        # Example format:
        # {
        #   "messages": [
        #     {
        #       "id": "...",
        #       "body": "reset",
        #       "fromMe": false,
        #       "self": 0,
        #       "isForwarded": false,
        #       "author": "6587788080@c.us",
        #       "time": "1749049642",
        #       "chatId": "6587788080@c.us",
        #       "type": "chat",
        #       "senderName": "Four Solutions",
        #       "caption": null,
        #       "quotedMsgId": null,
        #       "chatName": "6587788080@c.us"
        #     }
        #   ],
        #   "instanceId": "VAN388218473"
        # }
        if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
            messages = payload["messages"]

        # ─── 2) If not found above, check for the 1msg “360dialog” wrapper format ───
        # Example format:
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
        if messages is None:
            data_section = payload.get("data")
            if isinstance(data_section, dict):
                inner_payload = data_section.get("payload")
                if isinstance(inner_payload, dict):
                    wrapped360 = inner_payload.get("360dialog")
                    if isinstance(wrapped360, dict):
                        messages = wrapped360.get("messages", [])

        # ─── 3) If still not found, fallback to original “entry→changes→value→messages” ─
        # Example format (Facebook Graph callback):
        # {
        #   "entry": [
        #     {
        #       "changes": [
        #         {
        #           "value": {
        #             "messages": [
        #               {
        #                 "from": "659XXXXXXXX",
        #                 "type": "text",
        #                 "text": { "body": "hello bot" }
        #               }
        #             ]
        #           }
        #         }
        #       ]
        #     }
        #   ]
        # }
        if messages is None or not isinstance(messages, list) or len(messages) == 0:
            entry_list = payload.get("entry")
            if isinstance(entry_list, list) and len(entry_list) > 0:
                first_entry = entry_list[0]
                changes_list = first_entry.get("changes")
                if isinstance(changes_list, list) and len(changes_list) > 0:
                    first_change = changes_list[0]
                    value_section = first_change.get("value", {})
                    messages = value_section.get("messages", [])

        # If we still have no messages array or it’s empty, return early
        if not isinstance(messages, list) or len(messages) == 0:
            return make_response("No messages to process", 200)

        # Now messages is guaranteed to be a non‐empty list
        message = messages[0]

        # ─── Extract “from_number” and “msg_type” according to which format we detected ───
        # Case A: 1msg “WhatsApp Web” wrapper uses “author” or “chatId” for sender,
        #         and “body” as text. It does not have “type":"text" in the same way.
        if "author" in message and "body" in message:
            # In this format, “author” is like “6587788080@c.us”. Split off “@c.us”:
            author_full = message.get("author", "")
            from_number = author_full.split("@")[0] if "@" in author_full else author_full
            msg_type    = "chat"  # treat this as a text/chat message
            text_body   = message.get("body", "").strip().lower()

        else:
            # Case B & C: “360dialog” wrapper or original Graph format have “from” and “type”
            from_number = message.get("from")
            msg_type    = message.get("type")
            text_body   = ""
            if msg_type == "text":
                text_body = message.get("text", {}).get("body", "").strip().lower()
            elif msg_type in ("interactive", "button_reply", "list_reply"):
                # For interactive messages we’ll handle payloads below
                pass

        if not from_number or not msg_type:
            # Something unexpected in the message object
            return make_response("Invalid message format", 200)

        # ─── Route by message type ────────────────────────────────────────────────
        # We unify both “chat” (WhatsApp Web) and “text” (360dialog/Graph) to a text flow
        if msg_type in ("text", "chat"):
            # If user sends “reset”, clear all states and show the *actual* main menu
            if text_body == "reset":
                clear_user_state("car", from_number)
                clear_user_state("bedbug", from_number)
                clear_user_state("mold", from_number)

                # Instead of sending a plain‐text prompt, call the real send_main_menu()
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return make_response("User session reset → main menu sent", 200)

            # If user types “need help on car” (case‐insensitive), start Car flow
            if "need help on car" in text_body:
                clear_user_state("bedbug", from_number)
                clear_user_state("mold", from_number)
                send_template_message(
                    to=from_number,
                    template_name="car_fum_menu",
                    template_params=[]
                )
                return make_response("Car fumigation menu sent", 200)

            # If user types “need help on pest”, start Bedbug flow
            if "need help on pest" in text_body:
                clear_user_state("car", from_number)
                clear_user_state("mold", from_number)
                send_template_message(
                    to=from_number,
                    template_name="Bedbug_Main_Menu",
                    template_params=[]
                )
                return make_response("Bedbug menu sent", 200)

            # If user types “need help on mold”, start Mold flow
            if "need help on mold" in text_body:
                clear_user_state("car", from_number)
                clear_user_state("bedbug", from_number)
                send_template_message(
                    to=from_number,
                    template_name="Mold_Main_Menu",
                    template_params=[]
                )
                return make_response("Mold menu sent", 200)

            # Otherwise, delegate to whichever flow has an active state
            car_state    = get_user_state("car", from_number)
            bedbug_state = get_user_state("bedbug", from_number)
            mold_state   = get_user_state("mold", from_number)

            if car_state:
                return car_fumigation.handle_car_fumigation_flow(from_number, message, car_state)
            elif bedbug_state:
                return bedbug.handle(from_number, message, bedbug_state)
            elif mold_state:
                return mold.handle(from_number, message, mold_state)
            else:
                # No active flow: send a generic unrecognized‐text template
                send_template_message(
                    to=from_number,
                    template_name="Fallback_Unrecognized",
                    template_params=[
                        (
                            "Sorry, I didn’t understand that. "
                            "You can type ‘reset’ to return to the main menu."
                        )
                    ]
                )
                return make_response("Unsupported text fallback sent", 200)

        elif msg_type == "interactive":
            # For interactive replies (buttons, list selections), extract user response
            interactive = message.get("interactive", {})
            i_type      = interactive.get("type")

            # BUTTON_REPLY
            if i_type == "button_reply":
                button_id   = interactive["button_reply"].get("id")
                button_text = interactive["button_reply"].get("title", "").strip().lower()

                car_state    = get_user_state("car", from_number)
                bedbug_state = get_user_state("bedbug", from_number)
                mold_state   = get_user_state("mold", from_number)

                if car_state:
                    return car_fumigation.handle_car_fumigation_flow(from_number, message, car_state)
                elif bedbug_state:
                    return bedbug.handle(from_number, message, bedbug_state)
                elif mold_state:
                    return mold.handle(from_number, message, mold_state)
                else:
                    # No active flow: send the real main menu again
                    car_fumigation.send_main_menu(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return make_response("No active flow → main menu re-sent", 200)

            # LIST_REPLY
            elif i_type == "list_reply":
                list_id    = interactive["list_reply"]["id"]
                list_text  = interactive["list_reply"]["title"].strip().lower()

                car_state    = get_user_state("car", from_number)
                bedbug_state = get_user_state("bedbug", from_number)
                mold_state   = get_user_state("mold", from_number)

                if car_state:
                    return car_fumigation.handle_car_fumigation_flow(from_number, message, car_state)
                elif bedbug_state:
                    return bedbug.handle(from_number, message, bedbug_state)
                elif mold_state:
                    return mold.handle(from_number, message, mold_state)
                else:
                    # No active flow: send the real main menu again
                    car_fumigation.send_main_menu(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return make_response("No active flow → main menu re-sent", 200)

            else:
                # Unhandled interactive type
                send_text_message(
                    to=from_number,
                    body=(
                        "Sorry, I didn’t understand your selection. Please try again "
                        "or type ‘reset’ to return to the main menu."
                    )
                )
                return make_response("Unhandled interactive type", 200)

        else:
            # Any other message type (image, video, audio, stickers, etc.)
            send_template_message(
                to=from_number,
                template_name="Fallback_Unhandled_Type",
                template_params=[
                    (
                        "Sorry, I can’t handle that type of message. "
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
