# dispatcher.py

import os
import json
from flask import Flask, request, Response

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_text_message
)

from flows.car_fumigation import (
    handle_car_fumigation_flow,
    send_main_menu as send_car_main_menu
)
from flows.bedbug import handle_bedbug_flow
from flows.mold import handle_mold_flow

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def incoming_webhook() -> Response:
    """
    Entry point for every incoming webhook from 1msg. We inspect
    request.json, figure out the phone number, body text or button,
    and route into the appropriate flow (car, bedbug, mold) or
    show the main menu if nothing matches.
    """
    data = request.get_json(force=True)
    # Always print the raw incoming JSON for debugging:
    print(">>>> RAW INCOMING JSON:", json.dumps(data, indent=2))

    # 1msg always wraps your incoming messages under "messages": []
    # It may contain "messages" or "ack" or "status", etc. We only
    # care about "messages" when a user actually sends text / taps a button.
    messages = data.get("messages") or []
    if not messages:
        # e.g. an ACK/status event; ignore
        return Response(status=200)

    msg = messages[0]
    phone_with_suffix = msg.get("chatId", "")
    # chatId always looks like "6591234567@c.us"
    phone_no = phone_with_suffix.replace("@c.us", "")

    # Extract what kind of message this is:
    msg_type = msg.get("type")  # "chat", "button", "interactive", etc.

    # If this is a text message:
    if msg_type == "chat":
        body_text = msg.get("body", "").strip().lower()

        # 1) If user typed exactly "reset", clear all state & show main menu
        if body_text == "reset":
            print(f"[DEBUG] RESET branch hit (body_text == 'reset'), will send main_menu_v2")
            clear_user_state("car", phone_no)
            clear_user_state("bedbug", phone_no)
            clear_user_state("mold", phone_no)

            # Send the “main_menu_v2” template:
            resp = send_template_message(
                to=phone_no,
                template_name="main_menu_v2",
                template_params=["there"]
            )
            print(f"[DEBUG] send_template_message(main_menu_v2) → {resp}")
            return Response(status=200)

        # 2) Otherwise, check if the user is currently inside one of our flows:
        user_flow_car    = get_user_state("car", phone_no)
        user_flow_bedbug = get_user_state("bedbug", phone_no)
        user_flow_mold   = get_user_state("mold", phone_no)

        if user_flow_car is not None:
            # Pass control to the Car Fumigation flow
            print(f"[DEBUG] Routing into car_fumigation: text='{body_text}'")
            return handle_car_fumigation_flow(
                to_chat_id=phone_with_suffix,
                message=msg,
                user_state=user_flow_car,
                api_key=os.getenv("WHATSAPP_TOKEN", ""),
                base_url=os.getenv("BASE_URL", "")
            )

        if user_flow_bedbug is not None:
            print(f"[DEBUG] Routing into bedbug flow: text='{body_text}'")
            return handle_bedbug_flow(
                from_number=phone_with_suffix,
                message=msg,
                user_state=user_flow_bedbug
            )

        if user_flow_mold is not None:
            print(f"[DEBUG] Routing into mold flow: text='{body_text}'")
            return handle_mold_flow(
                from_number=phone_with_suffix,
                message=msg,
                user_state=user_flow_mold
            )

        # 3) Fallback: No flow matched, no “reset.” Just show main menu again:
        print(f"[DEBUG] FALLBACK chat (“{body_text}”), resending main_menu_v2")
        resp = send_template_message(
            to=phone_no,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        print(f"[DEBUG] send_template_message(main_menu_v2) → {resp}")
        return Response(status=200)

    # If the user tapped a “Button” (type == "button"), or an interactive reply,
    # we treat it exactly like they tapped one of our menu options. We look at “payload.”
    if msg_type in ["button", "interactive"]:
        # Extract the button payload:
        payload = ""
        # Standard “button” payload:
        if msg.get("type") == "button":
            payload = msg["button"].get("payload", "")
        # Or interactive.button_reply:
        elif msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            payload = msg["interactive"]["button_reply"].get("id", "")

        payload_lower = payload.lower()
        print(f"[DEBUG] INCOMING BUTTON/INTERACTIVE payload='{payload_lower}' from={phone_no}")

        # 1) Did they tap “Need help on Pest!”? That should start the car-fumigation flow.
        if payload_lower == "need help on pest!":
            clear_user_state("car", phone_no)
            initial_state = {"step": "select_pest_type"}
            set_user_state("car", phone_no, initial_state)

            # Immediately send the “Pest Control” list:
            return handle_car_fumigation_flow(
                to_chat_id=phone_with_suffix,
                message=msg,
                user_state=initial_state,
                api_key=os.getenv("WHATSAPP_TOKEN", ""),
                base_url=os.getenv("BASE_URL", "")
            )

        # 2) Did they tap “Need help on Mold!”? That should start the mold flow.
        if payload_lower == "need help on mold!":
            clear_user_state("mold", phone_no)
            new_state = {"step": "mold_option", "affected_areas": []}
            set_user_state("mold", phone_no, new_state)

            return handle_mold_flow(
                from_number=phone_with_suffix,
                message=msg,
                user_state=new_state
            )

        # 3) Did they tap “Live Human”? (We’ll just send a polite text.)
        if payload_lower == "live human":
            send_text_message({
                "to": phone_no,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Sure—connecting you to a live agent now. Please wait…"}
            })
            return Response(status=200)

        # 4) Otherwise, maybe they’re already in the bedbug flow?
        user_flow_car    = get_user_state("car", phone_no)
        user_flow_bedbug = get_user_state("bedbug", phone_no)
        user_flow_mold   = get_user_state("mold", phone_no)

        if user_flow_car is not None:
            print(f"[DEBUG] BUTTON → Routing into car_fumigation_flow (payload={payload_lower})")
            return handle_car_fumigation_flow(
                to_chat_id=phone_with_suffix,
                message=msg,
                user_state=user_flow_car,
                api_key=os.getenv("WHATSAPP_TOKEN", ""),
                base_url=os.getenv("BASE_URL", "")
            )

        if user_flow_bedbug is not None:
            print(f"[DEBUG] BUTTON → Routing into bedbug flow (payload={payload_lower})")
            return handle_bedbug_flow(
                from_number=phone_with_suffix,
                message=msg,
                user_state=user_flow_bedbug
            )

        if user_flow_mold is not None:
            print(f"[DEBUG] BUTTON → Routing into mold flow (payload={payload_lower})")
            return handle_mold_flow(
                from_number=phone_with_suffix,
                message=msg,
                user_state=user_flow_mold
            )

        # 5) If none of the above matched, just re-send the main menu:
        print(f"[DEBUG] BUTTON fallback (payload={payload_lower}), re-sending main_menu_v2")
        resp = send_template_message(
            to=phone_no,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        print(f"[DEBUG] send_template_message(main_menu_v2) → {resp}")
        return Response(status=200)

    # Any other message types (read receipts, location events, etc.) → ignore
    return Response(status=200)

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
