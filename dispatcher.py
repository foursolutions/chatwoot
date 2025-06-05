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


def normalize_phone(wa_id: str) -> str:
    """
    Strips off “@c.us” from a WhatsApp ID so that we only pass digits to 1msg.
    e.g. "6587788080@c.us" → "6587788080"
    """
    if "@" in wa_id:
        return wa_id.split("@")[0]
    return wa_id


@app.route("/webhook", methods=["POST"])
def webhook():
    raw = request.get_data(as_text=True)
    payload = json.loads(raw)

    # Log the incoming payload
    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    messages = payload.get("messages") or []
    if not messages:
        return Response(status=200)

    msg = messages[0]
    wa_id    = msg.get("chatId") or msg.get("author")    # e.g. "6587788080@c.us"
    from_id  = msg.get("author") or msg.get("chatId")    # same thing
    msg_type = msg.get("type")                           # e.g. "chat", "button", "interactive"
    body_text = (msg.get("body") or "").strip()

    # Normalize phone number (strip off "@c.us")
    phone_no = normalize_phone(from_id)

    # ─── 1) RESET BRANCH ─────────────────────────────────────────────────────────
    if msg_type == "chat" and body_text.lower() == "reset":
        # Clear any in-progress flow states:
        clear_user_state("car_fumigation", wa_id)
        clear_user_state("bedbug", wa_id)
        clear_user_state("mold", wa_id)

        print("[DEBUG] RESET branch hit (body_text == 'reset'), will send main_menu_v2")

        # Send the Main Menu template back to the user (no “@c.us”, just digits)
        resp = send_template_message(
            to=phone_no,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        print(f"[DEBUG] send_template_message(main_menu_v2) → {resp}")

        return Response(status=200)


    # ─── 2) ROUTE INTO CAR-FUMIGATION FLOW ────────────────────────────────────────
    car_state = get_user_state("car_fumigation", wa_id) or {}
    if (
        (msg_type in ["button", "interactive"] and body_text.lower() == "need help on pest!")
        or car_state.get("step")
    ):
        handle_car_fumigation_flow(
            from_number=wa_id,
            message=msg,
            api_key=os.getenv("ONE_MSG_TOKEN"),
            base_url=os.getenv("ONE_MSG_BASE_URL")
        )
        return Response(status=200)


    # ─── 3) ROUTE INTO BEDBUG FLOW ───────────────────────────────────────────────
    bedbug_state = get_user_state("bedbug", wa_id) or {}
    if (
        (msg_type in ["button", "interactive"] and body_text.lower().startswith("need help on bedbug"))
        or bedbug_state.get("step")
    ):
        handle_bedbug_flow(from_number=wa_id, message=msg, user_state=bedbug_state)
        return Response(status=200)


    # ─── 4) ROUTE INTO MOLD FLOW ─────────────────────────────────────────────────
    mold_state = get_user_state("mold", wa_id) or {}
    if (
        (msg_type in ["button", "interactive"] and body_text.lower() == "need help on mold!")
        or mold_state.get("step")
    ):
        handle_mold_flow(from_number=wa_id, message=msg, user_state=mold_state)
        return Response(status=200)


    # ─── 5) FALLBACK FOR ANY OTHER “CHAT” ────────────────────────────────────────
    if msg_type == "chat":
        print(f"[DEBUG] FALLBACK chat (“{body_text}”), resending main_menu_v2")
        resp = send_template_message(
            to=phone_no,
            template_name="main_menu_v2",
            template_params=["there"]
        )
        print(f"[DEBUG] send_template_message(main_menu_v2) → {resp}")
        return Response(status=200)

    # Any other message types (e.g. read receipts, location, etc.) → do nothing
    return Response(status=200)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
