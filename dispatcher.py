# dispatcher.py
import os
import json
from fastapi import FastAPI, Request, Response

from helpers import (
    send_text_message,
    send_interactive_message,
    send_template_message,
    get_user_state,
    set_user_state,
    clear_user_state
)

# Import your actual flow handlers
from flows.car_fumigation import handle_car_fumigation_flow
from flows.bedbug import handle_bedbug_flow
from flows.mold import handle_mold_flow

app = FastAPI()


@app.post("/webhook")
async def receive_message(request: Request):
    payload = await request.json()
    print(">>>> RAW INCOMING JSON:", json.dumps(payload))

    # ——————————————  
    # 1) Extract “messages” array (1MSG v2 vs. older wrappers vs. FB Graph)
    # ——————————————
    messages = None

    # 1MSG v2: {"messages": [ ... ], "instanceId": "..."}
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        messages = payload["messages"]

    # older 1MSG / 360dialog wrapper: data → payload → 360dialog → messages
    if messages is None:
        data_section = payload.get("data", {})
        if isinstance(data_section, dict):
            p = data_section.get("payload", {})
            if isinstance(p, dict):
                w360 = p.get("360dialog", {})
                if isinstance(w360, dict):
                    messages = w360.get("messages", [])

    # Facebook Graph style: entry → changes → value → messages
    if not messages:
        entry_list = payload.get("entry", [])
        if entry_list:
            changes_list = entry_list[0].get("changes", [])
            if changes_list:
                val = changes_list[0].get("value", {})
                messages = val.get("messages", [])

    if not messages:
        return Response(status_code=200, content="No messages to process")

    message = messages[0]

    # ——————————————  
    # 2) Extract sender + message text / type
    # ——————————————
    if "author" in message and "body" in message:
        # 1MSG “WhatsApp Web” wrapper
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

    # Normalize to E.164 (+…)
    if not from_number.startswith("+"):
        from_number = "+" + from_number

    # ——————————————  
    # 3) If user typed exactly “reset” → clear states & show main menu
    # ——————————————
    if msg_type == "text" and text_body == "reset":
        # Clear any in‐progress state for all flows
        clear_user_state("carfum", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        menu_payload = {
            "to": from_number,
            "type": "interactive",
            "messaging_product": "whatsapp",
            "interactive": {
                "type": "button",
                "body": {
                    "text": (
                        "Hi there, thanks for reaching out to Four Solutions! "
                        "I'm Solvia, your fun and friendly chatbot.\n"
                        "How may I help you today? (Tap \"Live Human\" anytime, or choose one of the options below.)"
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
        result = send_interactive_message(menu_payload)
        print("[DEBUG] send_interactive_message →", result)
        return Response(status_code=200, content="Interactive menu sent")

    # ——————————————  
    # 4) If user tapped an interactive button reply
    # ——————————————
    if msg_type == "interactive" and message["interactive"].get("type") == "button_reply":
        payload_id = message["interactive"]["button_reply"]["id"].lower()

        if payload_id == "help_pest":
            clear_user_state("carfum", from_number)
            clear_user_state("mold", from_number)

            set_user_state("bedbug", from_number, {"step": "start"})
            return handle_bedbug_flow(
                from_number,
                message,
                get_user_state("bedbug", from_number)
            )

        if payload_id == "help_mold":
            clear_user_state("carfum", from_number)
            clear_user_state("bedbug", from_number)

            set_user_state("mold", from_number, {"step": "start"})
            return handle_mold_flow(
                from_number,
                message,
                get_user_state("mold", from_number)
            )

        if payload_id == "live_human":
            clear_user_state("carfum", from_number)
            clear_user_state("bedbug", from_number)
            clear_user_state("mold", from_number)

            send_text_message(
                to_number=from_number,
                text="Okay—connecting you to a live human agent now!"
            )
            return Response(status_code=200, content="Live human handoff")

        # Unrecognized button ID
        send_text_message(
            to_number=from_number,
            text="Sorry, I didn’t understand that button."
        )
        return Response(status_code=200, content="Unknown button pressed")

    # ——————————————  
    # 5) If user tapped an interactive list reply
    # ——————————————
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        # Delegate to whichever flow has an active “step”
        if get_user_state("bedbug", from_number).get("step"):
            return handle_bedbug_flow(
                from_number,
                message,
                get_user_state("bedbug", from_number)
            )
        if get_user_state("mold", from_number).get("step"):
            return handle_mold_flow(
                from_number,
                message,
                get_user_state("mold", from_number)
            )
        if get_user_state("carfum", from_number).get("step"):
            return handle_car_fumigation_flow(
                from_number,
                message,
                get_user_state("carfum", from_number)
            )

        # No flow in progress—fallback
        send_text_message(
            to_number=from_number,
            text="Sorry, I cannot handle that reply right now. Type 'reset' to start over."
        )
        return Response(status_code=200, content="List reply fallback")

    # ——————————————  
    # 6) USER SENT FREE TEXT
    # ——————————————
    if msg_type == "text":
        # a) If bedbug/mold/car flow in progress, delegate
        if get_user_state("bedbug", from_number).get("step"):
            return handle_bedbug_flow(
                from_number,
                message,
                get_user_state("bedbug", from_number)
            )
        if get_user_state("mold", from_number).get("step"):
            return handle_mold_flow(
                from_number,
                message,
                get_user_state("mold", from_number)
            )
        if get_user_state("carfum", from_number).get("step"):
            return handle_car_fumigation_flow(
                from_number,
                message,
                get_user_state("carfum", from_number)
            )

        # b) No flow in progress—look for keyword triggers
        if "need help on pest" in text_body:
            set_user_state("bedbug", from_number, {"step": "start"})
            return handle_bedbug_flow(
                from_number,
                message,
                get_user_state("bedbug", from_number)
            )

        if "need help on mold" in text_body:
            set_user_state("mold", from_number, {"step": "start"})
            return handle_mold_flow(
                from_number,
                message,
                get_user_state("mold", from_number)
            )

        if "need help on car" in text_body:
            set_user_state("carfum", from_number, {"step": "start"})
            return handle_car_fumigation_flow(
                from_number,
                message,
                get_user_state("carfum", from_number)
            )

        # c) Final fallback for free text
        send_text_message(
            to_number=from_number,
            text="Please type ‘need help on pest’, ‘need help on mold’ or ‘need help on car’ to begin."
        )
        return Response(status_code=200, content="Free‐text fallback")

    # ——————————————  
    # 7) ANY OTHER msg_type (ignored)
    # ——————————————
    return Response(status_code=200, content="Ignored non‐text/non‐interactive message")
