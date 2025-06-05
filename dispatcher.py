# begin dispatcher.py
import os
import json
from flask import Flask, request, Response
from helpers import (
    send_text_message,
    send_interactive_message,
    send_template_message,
    get_user_state,
    set_user_state,
    clear_user_state
)
from flows.car_fumigation import handle_car_fumigation_flow
from flows.bedbug import handle_bedbug_flow
from flows.mold import handle_mold_flow

app = Flask(__name__)

# ── Load environment variables ─────────────────────────────────────────────────
VERIFY_TOKEN       = os.environ.get("VERIFY_TOKEN", "")
API_KEY            = os.environ.get("1MSG_API_KEY", "")
BASE_URL           = os.environ.get("1MSG_BASE_URL", "")        # e.g. https://api.1msg.io/VAN123456
NAMESPACE          = os.environ.get("1MSG_NAMESPACE", "")       # e.g. 94d66366_9ec1_43a3_a84c_46039bd33ef5
LANG_CODE          = os.environ.get("1MSG_LANG_CODE", "en")     # e.g. "en"
MAIN_MENU_TEMPLATE = os.environ.get("MAIN_MENU_TEMPLATE", "main_menu_v2")

# ── Webhook verification (GET) ────────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification token mismatch", 403

# ── Main webhook endpoint (POST) ──────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def receive_message():
    raw_payload = request.get_data(as_text=True)
    try:
        payload = json.loads(raw_payload)
    except:
        payload = request.get_json(force=True)

    print(">>>> RAW INCOMING JSON:", json.dumps(payload, indent=2))

    # ── Step 0: ignore any “ack” (delivery/read receipts) from 1msg ───────────
    if "ack" in payload:
        return Response(status=200)

    # ── Step 1: if there’s no “messages” array, nothing to do ─────────────────
    if "messages" not in payload or not isinstance(payload["messages"], list):
        return Response(status=200)

    entry = payload["messages"][0]
    msg_type = entry.get("type", "")

    # ── Step 2: extract the “from” phone number ───────────────────────────────
    raw_from = entry.get("from", "") or entry.get("author", "")
    from_number = raw_from.split("@")[0] if "@" in raw_from else raw_from

    # ── Step 3: if this is plain‐text chat (type=="chat"), grab text_body ────
    text_body = ""
    if msg_type == "chat":
        text_body = entry.get("body", "").strip().lower()

    # ── Step 4: if user typed “reset”, clear all states and send main-menu ───
    if msg_type == "chat" and text_body == "reset":
        clear_user_state("car", from_number)
        clear_user_state("bedbug", from_number)
        clear_user_state("mold", from_number)

        # Send the main menu as a template
        send_template_message(
            to=from_number,
            namespace=NAMESPACE,
            template_name=MAIN_MENU_TEMPLATE,
            params=[{"type": "body", "parameters": [{"type": "text", "text": "there"}]}],
            language={"policy": "deterministic", "code": LANG_CODE}
        )
        return Response(status=200)

    # ── Step 5: handle button clicks (old‐style “type":"button” quick‐reply) ──
    if msg_type == "button":
        payload_text = entry.get("body", "").strip().lower()
        # “Need help on Pest!” or custom payload “help_pest”
        if payload_text in ["need help on pest!", "help_pest"]:
            # Initialize “car” flow, store an empty dict as state
            set_user_state("car", from_number, {})
            user_state = get_user_state("car", from_number)
            return handle_car_fumigation_flow(from_number, entry, user_state, BASE_URL)
        # “Need help on Mold!” or custom payload “help_mold”
        if payload_text in ["need help on mold!", "help_mold"]:
            set_user_state("mold", from_number, {})
            user_state = get_user_state("mold", from_number)
            return handle_mold_flow(from_number, entry, user_state, BASE_URL)
        # “Live Human”
        if payload_text in ["live_human"]:
            send_text_message({
                "to": from_number,
                "type": "text",
                "text": {"body": "Sure—one of our agents will be with you shortly."},
                "messaging_product": "whatsapp"
            })
            return Response(status=200)

    # ── Step 5b: handle new‐style interactive (1msg) payloads ────────────────
    if msg_type == "interactive":
        interactive = entry.get("interactive", {})
        # “button_reply” includes .get("id")
        button_reply = interactive.get("button_reply")
        if button_reply:
            button_id = button_reply.get("id", "")
            if button_id == "help_pest":
                set_user_state("car", from_number, {})
                user_state = get_user_state("car", from_number)
                return handle_car_fumigation_flow(from_number, entry, user_state, BASE_URL)
            if button_id == "help_mold":
                set_user_state("mold", from_number, {})
                user_state = get_user_state("mold", from_number)
                return handle_mold_flow(from_number, entry, user_state, BASE_URL)
            if button_id == "live_human":
                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "text": {"body": "Sure—one of our agents will be with you shortly."},
                    "messaging_product": "whatsapp"
                })
                return Response(status=200)

    # ── Step 6: if user is “in” the car flow already, delegate to that flow ───
    user_state_car = get_user_state("car", from_number)
    if user_state_car is not None:
        return handle_car_fumigation_flow(from_number, entry, user_state_car, BASE_URL)

    # ── Step 6b: if user is “in” the bedbug flow, delegate ──────────────────
    user_state_bedbug = get_user_state("bedbug", from_number)
    if user_state_bedbug is not None:
        return handle_bedbug_flow(from_number, entry, user_state_bedbug, BASE_URL)

    # ── Step 6c: if user is “in” the mold flow, delegate ────────────────────
    user_state_mold = get_user_state("mold", from_number)
    if user_state_mold is not None:
        return handle_mold_flow(from_number, entry, user_state_mold, BASE_URL)

    # ── Step 7: any other plain chat/text → re‐send main menu template ────────
    if msg_type == "chat":
        send_template_message(
            to=from_number,
            namespace=NAMESPACE,
            template_name=MAIN_MENU_TEMPLATE,
            params=[{"type": "body", "parameters": [{"type": "text", "text": "there"}]}],
            language={"policy": "deterministic", "code": LANG_CODE}
        )
        return Response(status=200)

    return Response(status=200)
# end dispatcher.py
