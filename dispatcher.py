# dispatcher.py

import os
import json
from fastapi import FastAPI, Request, Response
from helpers import send_text_message, send_interactive_message, get_user_state, set_user_state, clear_user_state
# from car_fumigation import handle_car_fumigation
# from bedbug import handle_bedbug_flow
# from mold import handle_mold_flow

app = FastAPI()


@app.post("/webhook")
async def receive_message(request: Request):
    payload = await request.json()
    print(">>>> RAW INCOMING JSON:", json.dumps(payload))

    # ——— Extract the “messages” array from 1msg’s envelope ———
    messages = None

    # 1) Newer 1msg wrapper: payload["messages"]
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        messages = payload["messages"]

    # 2) Older 1msg wrapper: payload["data"]["payload"]["360dialog"]["messages"]
    if messages is None:
        data_section = payload.get("data", {})
        if isinstance(data_section, dict):
            p = data_section.get("payload", {})
            if isinstance(p, dict):
                w360 = p.get("360dialog", {})
                if isinstance(w360, dict):
                    messages = w360.get("messages", [])

    # 3) Facebook‐Graph style (entry→changes→value→messages)
    if not messages:
        entry_list = payload.get("entry", [])
        if entry_list:
            changes_list = entry_list[0].get("changes", [])
            if changes_list:
                val = changes_list[0].get("value", {})
                messages = val.get("messages", [])

    if not messages:
        return Response(status_code=200, content="No messages")

    message = messages[0]

    # ——— Extract sender phone and type/body ———
    if "author" in message and "body" in message:
        # 1msg “WhatsApp Web” wrapper
        author_full = message.get("author", "")
        from_number = author_full.split("@")[0]
        msg_type = "text"
        text_body = message.get("body", "").strip().lower()
    else:
        # 360dialog / Graph style
        raw_from = message.get("from", "")
        if "@" in raw_from:
            from_number = raw_from.split("@")[0]
        else:
            from_number = raw_from

        msg_type = message.get("type", "")
        text_body = ""
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()

    if not from_number or not msg_type:
        return Response(status_code=200, content="Malformed message")

    #
    # ——— 1) USER SAYS “reset” (send interactive button menu) ———
    #
    if msg_type == "text" and text_body == "reset":
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        interactive_payload = {
            "to": from_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": (
                        "Hi there, thanks for reaching out to Four Solutions! "
                        "I'm Solvia, your fun and friendly chatbot.\n"
                        "How may I help you today? (Tap ‘Live Human’ anytime, "
                        "or choose one of the options below.)"
                    )
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "help_pest",
                                "title": "Need help on Pest!"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "help_mold",
                                "title": "Need help on Mold!"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "live_human",
                                "title": "Live Human"
                            }
                        }
                    ]
                }
            }
        }

        try:
            send_interactive_message(interactive_payload)
        except Exception as e:
            print("ERROR sending main menu (interactive):", e)

        return Response(status_code=200, content="Interactive main menu sent")

    #
    # ——— 2) USER TAPS ONE OF THOSE BUTTONS (“type”:“button”) ———
    #
    if msg_type == "button":
        btn = message.get("button", {})
        payload_id = btn.get("payload", "")

        if payload_id == "help_pest":
            clear_user_state("car", from_number)
            clear_user_state("mold", from_number)

            set_user_state("bedbug", from_number, {"step": "start"})
            # bedbug.handle_bedbug_flow(from_number)
            send_text_message(from_number, "Bedbug flow started… (your code here)")
            return Response(status_code=200, content="Bedbug flow triggered")

        if payload_id == "help_mold":
            clear_user_state("car", from_number)
            clear_user_state("bedbug", from_number)

            set_user_state("mold", from_number, {"step": "start"})
            # handle_mold_flow(from_number)
            send_text_message(from_number, "Mold flow started… (your code here)")
            return Response(status_code=200, content="Mold flow triggered")

        if payload_id == "live_human":
            clear_user_state("car", from_number)
            clear_user_state("bedbug", from_number)
            clear_user_state("mold", from_number)

            send_text_message(
                to=from_number,
                body="Okay, connecting you to a live human agent now!"
            )
            # (insert your live‐human logic here)
            return Response(status_code=200, content="Live human handoff")

        # Unknown button
        send_text_message(from_number, "Sorry, I didn’t understand that button.")
        return Response(status_code=200, content="Unknown button pressed")

    #
    # ——— 3) USER TYPES FREE TEXT ———
    #
    if msg_type == "text":
        # (Example: user might type “need help on pest” instead of tapping the button)
        if "need help on pest" in text_body:
            clear_user_state("car", from_number)
            clear_user_state("mold", from_number)

            set_user_state("bedbug", from_number, {"step": "start"})
            # bedbug.handle_bedbug_flow(from_number)
            send_text_message(from_number, "Bedbug flow started… (your code here)")
            return Response(status_code=200, content="Bedbug via text")

        if "need help on mold" in text_body:
            clear_user_state("car", from_number)
            clear_user_state("bedbug", from_number)

            set_user_state("mold", from_number, {"step": "start"})
            # handle_mold_flow(from_number)
            send_text_message(from_number, "Mold flow started… (your code here)")
            return Response(status_code=200, content="Mold via text")

        if "need help on car" in text_body:
            clear_user_state("bedbug", from_number)
            clear_user_state("mold", from_number)

            set_user_state("car", from_number, {"step": "start"})
            # handle_car_fumigation(from_number)
            send_text_message(from_number, "Car fumigation flow started… (your code here)")
            return Response(status_code=200, content="Car via text")

        # Otherwise, fallback:
        send_text_message(
            to=from_number,
            body="Please tap ‘Need help on Pest!’ or ‘Need help on Mold!’ to begin."
        )
        return Response(status_code=200, content="Fallback sent")

    #
    # ——— 4) ANY OTHER MESSAGE TYPES ———
    #
    return Response(status_code=200, content="Ignored non-text/button message")
