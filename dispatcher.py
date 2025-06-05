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

from flows.car_fumigation import handle_car_fumigation_flow, send_main_menu as send_car_main_menu
from flows.bedbug import handle_bedbug_flow
from flows.mold import handle_mold_flow, send_mold_option_prompt

app = Flask(__name__)

# ─── Helper to extract “pure” phone (no “@c.us”) ───────────────────────────────
def normalize_phone(wa_id: str) -> str:
    """
    Converts "6587788080@c.us" → "6587788080" (no “+”)
    """
    return wa_id.split("@")[0]


# ─── Main Webhook Endpoint ─────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    raw = request.get_data(as_text=True)
    payload = json.loads(raw)

    # Always log the incoming JSON
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # We expect “messages” array at top level
    messages = payload.get("messages") or []
    if not messages:
        return Response(status=200)

    msg = messages[0]
    wa_id   = msg.get("chatId") or msg.get("author")     # "6587788080@c.us"
    from_id = msg.get("author") or msg.get("chatId")     # sometimes “author”, sometimes “chatId”
    msg_type = msg.get("type")                           # "chat", "button", "interactive", etc.
    body_text = (msg.get("body") or "").strip()

    # Normalize phone (no “@c.us”)
    phone_no = normalize_phone(from_id)

    # Check for explicit “reset” command (in plain text)
    if msg_type == "chat" and body_text.lower() == "reset":
        # Clear any in‐progress flow state for all prefixes
        clear_user_state("car_fumigation", wa_id)
        clear_user_state("bedbug", wa_id)
        clear_user_state("mold", wa_id)
        # Send main menu template
        send_template_message(
            to=phone_no,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    # ─── ROUTE INTO CAR‐FUMIGATION FLOW ─────────────────────────────────────────
    #
    # 1) If user taps a “Need help on Pest!” button (payload or body), or has state for car_fumigation
    #
    car_state = get_user_state("car_fumigation", wa_id) or {}
    if (
        (msg_type in ["button", "interactive"] and body_text.lower() == "need help on pest!")
        or car_state.get("step")
    ):
        # Dispatch entire flow to car_fumigation
        handle_car_fumigation_flow(
            from_number=wa_id,
            message=msg,
            api_key=os.getenv("ONE_MSG_TOKEN"),
            base_url=os.getenv("ONE_MSG_BASE_URL")
        )
        return Response(status=200)

    # ─── ROUTE INTO BEDBUG FLOW ───────────────────────────────────────────────────
    #
    bedbug_state = get_user_state("bedbug", wa_id) or {}
    if (
        (msg_type in ["button", "interactive"] and body_text.lower().startswith("need help on bedbug"))
        or bedbug_state.get("step")
    ):
        handle_bedbug_flow(from_number=wa_id, message=msg, user_state=bedbug_state)
        return Response(status=200)

    # ─── ROUTE INTO MOLD FLOW ─────────────────────────────────────────────────────
    #
    mold_state = get_user_state("mold", wa_id) or {}
    if (
        (msg_type in ["button", "interactive"] and body_text.lower() == "need help on mold!")
        or mold_state.get("step")
    ):
        handle_mold_flow(from_number=wa_id, message=msg, user_state=mold_state)
        return Response(status=200)

    # ─── FALLBACK: ANY OTHER UNRECOGNIZED MESSAGE ─────────────────────────────────
    #
    # If the user types plain text that isn't “reset” or isn't handled by any flow, resend main menu.
    if msg_type == "chat":
        send_template_message(
            to=phone_no,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        return Response(status=200)

    # For any other message types (e.g., read receipts, location, etc.), do nothing
    return Response(status=200)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
