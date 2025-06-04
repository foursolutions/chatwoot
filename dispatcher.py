# dispatcher.py

import os
import json
from fastapi import FastAPI, Request, Response
from helpers import (
    send_text_message,
    send_interactive_message,
    get_user_state,
    set_user_state,
    clear_user_state
)
# Import your existing flows:
# from car_fumigation import handle_car_fumigation
# from bedbug import handle_bedbug_flow
# from mold import handle_mold_flow

app = FastAPI()

@app.post("/webhook")
async def receive_message(request: Request):
    payload = await request.json()
    print(">>>> RAW INCOMING JSON:", json.dumps(payload))

    # 1) 1msg “WhatsApp Web” wrapper (newer 1msg style)
    messages = None
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        messages = payload["messages"]

    # 2) 1msg “360dialog” wrapper (older version)
    if messages is None:
        data_section = payload.get("data", {})
        if isinstance(data_section, dict):
            inner = data_section.get("payload", {})
            if isinstance(inner, dict):
                w360 = inner.get("360dialog", {})
                if isinstance(w360, dict):
                    messages = w360.get("messages", [])

    # 3) Classic “Facebook Graph” wrapper
    if not messages:
        entry_list = payload.get("entry", [])
        if entry_list:
            changes_list = entry_list[0].get("changes", [])
            if changes_list:
                value_section = changes_list[0].get("value", {})
                messages = value_section.get("messages", [])

    if not messages:
        # No messages to process
        return Response(status_code=200, content="No messages")

    message = messages[0]

    # Extract sender (phone) and msg_type, msg_body
    if "author" in message and "body" in message:
        # 1msg “WhatsApp Web” wrapper
        author_full = message.get("author")
        from_number = author_full.split("@")[0]
        msg_type = "text"  # treat this as a text‐chat
        text_body = message.get("body", "").strip().lower()
    else:
        # Classic 360dialog or Graph
        from_number = message.get("from")          # e.g. "6587788080@c.us"
        if from_number and "@" in from_number:
            from_number = from_number.split("@")[0]
        msg_type = message.get("type")              # e.g. "text", "button", etc.

        text_body = ""
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()

    if not from_number or not msg_type:
        return Response(status_code=200, content="Malformed message")

    #
    #  ─── RESET / MAIN MENU ────────────────────────────────────────────────────────
    #
    # If user says “reset” (or “hi”), send an interactive button menu instead of a template.
    #
    if msg_type in ("text",) and text_body == "reset":
        # Clear any in‐progress flows
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Build interactive “quick‐reply button” payload
        interactive_payload = {
            "to":                from_number,
            "type":              "interactive",
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

        # Send interactive buttons
        try:
            send_interactive_message(interactive_payload)
        except Exception as e:
            print("ERROR sending main menu (interactive):", e)

        return Response(status_code=200, content="Main menu sent (interactive)")

    #
    #  ─── HANDLE QUICK-REPLY BUTTON (USER TAPS ONE) ─────────────────────────────────
    #
    if msg_type == "button":
        # message["button"]["id"] will be one of: "help_pest", "help_mold", "live_human"
        payload_button = message.get("button", {})
        btn_payload = payload_button.get("payload", "")

        # Need help on Pest! → Bedbug flow
        if btn_payload == "help_pest":
            # Clear any other flow
            clear_user_state("car", from_number)
            clear_user_state("mold", from_number)

            # Initialize bedbug flow state
            set_user_state("bedbug", from_number, {"step": "start"})
            # (Replace with your actual bedbug entry function)
            # bedbug.handle_bedbug_start(from_number)
            send_text_message(from_number, "Bedbug flow started... (your code here)")
            return Response(status_code=200, content="Bedbug flow triggered")

        # Need help on Mold! → Mold flow
        if btn_payload == "help_mold":
            clear_user_state("car", from_number)
            clear_user_state("bedbug", from_number)

            set_user_state("mold", from_number, {"step": "start"})
            # (Replace with your actual mold entry function)
            # handle_mold_flow(from_number)
            send_text_message(from_number, "Mold flow started... (your code here)")
            return Response(status_code=200, content="Mold flow triggered")

        # Live Human → hand off to agent
        if btn_payload == "live_human":
            # Clear all flows
            clear_user_state("car", from_number)
            clear_user_state("bedbug", from_number)
            clear_user_state("mold", from_number)

            # Example “handoff” text
            send_text_message(
                to=from_number,
                body=(
                    "Okay, connecting you to a live human agent now! "
                    "One moment, please."
                )
            )
            # (You’d integrate your agent‐handoff logic here)
            return Response(status_code=200, content="Live human handoff triggered")

        # Button payload unrecognized
        send_text_message(from_number, "Sorry, I didn’t understand that button.")
        return Response(status_code=200, content="Unknown button")

    #
    #  ─── HANDLE FREE-TEXT INPUT BY USER ───────────────────────────────────────────
    #
    # If user replies with normal text (not buttons), route to the correct flow
    #
    if msg_type == "text":
        # If user typed “need help on pest” (fallback free‐text)
        if "need help on pest" in text_body:
            clear_user_state("car", from_number)
            clear_user_state("mold", from_number)

            set_user_state("bedbug", from_number, {"step": "start"})
            # bedbug.handle_bedbug_start(from_number)
            send_text_message(from_number, "Bedbug flow started... (your code here)")
            return Response(status_code=200, content="Bedbug flow triggered via text")

        # If user typed “need help on mold”
        if "need help on mold" in text_body:
            clear_user_state("car", from_number)
            clear_user_state("bedbug", from_number)

            set_user_state("mold", from_number, {"step": "start"})
            # handle_mold_flow(from_number)
            send_text_message(from_number, "Mold flow started... (your code here)")
            return Response(status_code=200, content="Mold flow triggered via text")

        # If user typed “need help on car”
        if "need help on car" in text_body or "need help on pest" in text_body:
            # (Depending on how you worded “car” vs “pest”)
            clear_user_state("bedbug", from_number)
            clear_user_state("mold", from_number)

            set_user_state("car", from_number, {"step": "start"})
            # handle_car_fumigation(from_number)
            send_text_message(from_number, "Car fumigation flow started... (your code here)")
            return Response(status_code=200, content="Car flow triggered via text")

        # Add any additional free‐text handling here…

        # Otherwise, fallback
        send_text_message(
            to=from_number,
            body="Please tap ‘Need help on Pest!’ or ‘Need help on Mold!’ to begin."
        )
        return Response(status_code=200, content="Fallback fallback")

    #
    #  ─── OTHER TYPES (e.g. “image”, “audio”, “document”) ─────────────────────────
    #
    # You can handle other message types here if you want (e.g. users who send an image).
    #
    return Response(status_code=200, content="Ignored message type")

