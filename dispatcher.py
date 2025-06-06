# dispatcher.py

import os
import json
import redis
from flask import Flask, request, Response

from helpers import (
    send_text_message,
    send_template_message,
    send_list_message,
    API_KEY_1MSG,
    BASE_URL_1MSG,
    NAMESPACE_1MSG,
    PHONE_NUMBER_ID,
    MAIN_MENU_TEMPLATE
)
from flows.car_fumigation import handle_car_fumigation_flow
from flows.bedbug import handle_bedbug_flow
from flows.mold import handle_mold_flow

app = Flask(__name__)

# ─── Redis setup (for user-state storage) ──────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "")
r = redis.from_url(REDIS_URL, decode_responses=True)


# ─── Helpers to get/set user state in Redis ─────────────────
def set_user_state(flow_prefix: str, user: str, state: dict):
    r.hset(f"{flow_prefix}:{user}", mapping=state)

def get_user_state(flow_prefix: str, user: str) -> dict:
    raw = r.hgetall(f"{flow_prefix}:{user}")
    return raw if raw else {}

def clear_user_state(flow_prefix: str, user: str):
    r.delete(f"{flow_prefix}:{user}")


# ─── Entry Point for WhatsApp Webhook ───────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    # 1msg sends {"messages": [...], "instanceId": "..."}
    messages = data.get("messages", [])
    if not messages:
        return Response(status=200)

    message = messages[0]
    msg_type = message.get("type")    # "chat", "button", or "interactive"
    body_text = message.get("body", "").strip().lower()
    from_number = message.get("author", message.get("from", ""))  # e.g. "6587788080@c.us"
    user_digits = from_number.split("@")[0]  # e.g. "6587788080"

    # ─── 1) RESET / unrecognized-text branch ──────────────────────────────────
    if body_text == "reset" or msg_type == "chat" and body_text not in (
        "need help on pest!", "need help on mold!", "live human"
    ):
        clear_user_state("car", user_digits)
        clear_user_state("bed", user_digits)
        clear_user_state("mold", user_digits)

        # Send the main menu template again
        resp = send_template_message(
            to=user_digits,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=["there"]
        )
        print(f"[DEBUG] RESET branch hit (body_text == 'reset'), will send main_menu_v2 → {resp}")
        return Response(status=200)

    # ─── 2) BUTTON-press logic: Gateway to each flow ─────────────────────────
    #    1msg now puts button taps into `msg_type == "button"`, with `body` == the button text.
    if msg_type == "button":
        button_text = message.get("body", "").strip().lower()

        if button_text == "need help on pest!":
            state = {}
            set_user_state("car", user_digits, {"step": "start"})
            return handle_car_fumigation_flow(
                to_chat_id=user_digits,
                message=message,
                api_key=API_KEY_1MSG,
                base_url=BASE_URL_1MSG
            )

        elif button_text == "need help on mold!":
            state = {"step": "mold_option", "affected_areas": []}
            set_user_state("mold", user_digits, state)
            return handle_mold_flow(
                from_number=user_digits,
                message=message,
                user_state=state
            )

        elif button_text == "live human":
            # If you want a “live human” fallback, just send a notice:
            send_text_message({
                "to": user_digits,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Please hold on, a human will join shortly…"}
            })
            return Response(status=200)

    # ─── 3) ROUTE INTO car_fumigation_flow if user is already mid-flow ─────────
    car_state = get_user_state("car", user_digits)
    if car_state:
        return handle_car_fumigation_flow(
            to_chat_id=user_digits,
            message=message,
            api_key=API_KEY_1MSG,
            base_url=BASE_URL_1MSG
        )

    # ─── 4) ROUTE INTO bedbug_flow if user is already mid-flow ───────────────
    bed_state = get_user_state("bed", user_digits)
    if bed_state:
        return handle_bedbug_flow(
            from_number=user_digits,
            message=message,
            user_state=bed_state
        )

    # ─── 5) ROUTE INTO mold_flow if user is already mid-flow ────────────────
    mold_state = get_user_state("mold", user_digits)
    if mold_state:
        return handle_mold_flow(
            from_number=user_digits,
            message=message,
            user_state=mold_state
        )

    # ─── 6) FALLBACK: If none of the above matched ───────────────────────────
    send_text_message({
        "to": user_digits,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Sorry, I didn’t understand that. Type 'reset' to start over." }
    })
    return Response(status=200)


if __name__ == "__main__":
    app.run(debug=True)
