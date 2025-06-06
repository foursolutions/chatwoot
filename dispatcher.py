# dispatcher.py

import os
import json
import logging
from flask import Flask, request, jsonify

# ----------------------------------------------------------------------
# Import each of your flow modules from the flows/ folder:
# (Your car_fumigation.py, bedbug.py, and mold.py already live under flows/)
# ----------------------------------------------------------------------
from flows import car_fumigation
from flows import bedbug
from flows import mold

from helpers import (
    get_user_state,
    set_user_state,
    pop_user_state,
    clear_user_state,
    send_text_message,
    send_interactive_message,
    send_template_message,
)

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)


@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Entry point for incoming 1MSG webhook. 
    Extracts user_id, message type, and either text, button_reply, or list_reply.
    Dispatches to the correct flow handler.
    """
    payload = request.get_json(force=True)
    logging.debug(f"Received raw message payload: {json.dumps(payload)}")

    messages = payload.get("messages", [])
    if not messages:
        # No actual user message (maybe an ACK); ignore.
        return jsonify({}), 200

    msg = messages[0]
    user_id = msg["chatId"]       # e.g. "6587788080@c.us"
    incoming_type = msg.get("type", "chat")
    incoming_body = msg.get("body", "").strip()
    interactive = msg.get("interactive", {})

    # ───────────────────────────────────────────────────────────────────────
    # Extract any button or list payload if present. 
    # 1MSG puts button IDs under msg["interactive"]["button_reply"]["id"]
    # and list IDs under msg["interactive"]["list_reply"]["id"].
    # Avoid KeyError by checking both.
    # ───────────────────────────────────────────────────────────────────────
    button_payload = ""
    if interactive:
        if "button_reply" in interactive:
            button_payload = interactive["button_reply"].get("id", "").strip()
        elif "list_reply" in interactive:
            button_payload = interactive["list_reply"].get("id", "").strip()

    # ───────────────────────────────────────────────────────────────────────
    # If the user typed “reset” (case-insensitive), clear all prefix state 
    # and re-send the main menu template.
    # ───────────────────────────────────────────────────────────────────────
    if incoming_type == "chat" and incoming_body.lower() == "reset":
        clear_user_state("prefix", user_id)
        # Assumes you have a helper called send_template_message(...) that
        # sends your MAIN MENU template. If you named it differently, adjust here.
        send_template_message(user_id)
        return jsonify({}), 200

    # ───────────────────────────────────────────────────────────────────────
    # Otherwise, check the user’s “prefix” state to know which flow they are in.
    # ───────────────────────────────────────────────────────────────────────
    user_state = get_user_state("prefix", user_id) or {}
    prefix = user_state.get("current_flow", None)

    # ───────────────────────────────────────────────────────────────────────
    # 1) Top-level buttons: “Need help on Pest!” or “Need help on Mold!”
    # When they tap one of these, clear any old state, set new prefix, 
    # and immediately send the appropriate interactive list.
    # ───────────────────────────────────────────────────────────────────────
    if incoming_type == "button":
        body_lower = incoming_body.lower()
        if body_lower == "need help on pest!":
            clear_user_state("prefix", user_id)
            set_user_state("prefix", user_id, {"current_flow": "pest"})
            # Show Pest Control Services list (from flows/car_fumigation)
            car_fumigation.send_pest_control_list(user_id)
            return jsonify({}), 200

        elif body_lower == "need help on mold!":
            clear_user_state("prefix", user_id)
            set_user_state("prefix", user_id, {"current_flow": "mold"})
            # Show Mold Service list (from flows/mold)
            mold.send_mold_service_list(user_id)
            return jsonify({}), 200

    # ───────────────────────────────────────────────────────────────────────
    # 2) Under “Pest” flow: they tapped a row in the Pest list (e.g. car_fumigation, bedbug)
    # ───────────────────────────────────────────────────────────────────────
    if prefix == "pest" and button_payload == "car_fumigation":
        # Remember they chose Car Fumigation
        set_user_state("prefix", user_id, {"current_flow": "pest", "service": "car_fumigation"})
        # Kick off your existing Car Fumigation flow logic
        car_fumigation.handle_car_fumigation_start(user_id)
        return jsonify({}), 200

    if prefix == "pest" and button_payload == "bedbug":
        set_user_state("prefix", user_id, {"current_flow": "pest", "service": "bedbug"})
        bedbug.handle_bedbug_start(user_id)
        return jsonify({}), 200

    # Add additional pest services here (e.g. if you had rodent → rodent.handle_start, etc.)

    # ───────────────────────────────────────────────────────────────────────
    # 3) Under “Mold” flow: they tapped a row in the Mold list (e.g. mold_inspection, mold_remediation)
    # ───────────────────────────────────────────────────────────────────────
    if prefix == "mold" and button_payload == "mold_inspection":
        set_user_state("prefix", user_id, {"current_flow": "mold", "service": "mold_inspection"})
        mold.handle_mold_inspection_start(user_id)
        return jsonify({}), 200

    if prefix == "mold" and button_payload == "mold_remediation":
        set_user_state("prefix", user_id, {"current_flow": "mold", "service": "mold_remediation"})
        mold.handle_mold_remediation_start(user_id)
        return jsonify({}), 200

    # ───────────────────────────────────────────────────────────────────────
    # 4) If they are already *inside* one of those flows (pest or mold) but sending free-text
    #    we must route the incoming chat text to the appropriate “next” handler in the flow.
    #    For example, once car_fumigation.handle_car_fumigation_start(...) has asked a question
    #    (“What’s your car model?”), the reply will come back as type="chat", so dispatch it:
    # ───────────────────────────────────────────────────────────────────────

    # Pest → Car Fumigation “next” step (they reply to the question asked in handle_start):
    if prefix == "pest" and user_state.get("service") == "car_fumigation" and incoming_type == "chat":
        car_fumigation.handle_car_fumigation_next(user_id, incoming_body)
        return jsonify({}), 200

    # Pest → Bedbug “next” step:
    if prefix == "pest" and user_state.get("service") == "bedbug" and incoming_type == "chat":
        bedbug.handle_bedbug_next(user_id, incoming_body)
        return jsonify({}), 200

    # Mold → Inspection “next” step:
    if prefix == "mold" and user_state.get("service") == "mold_inspection" and incoming_type == "chat":
        mold.handle_mold_next(user_id, incoming_body)
        return jsonify({}), 200

    # Mold → Remediation “next” step:
    if prefix == "mold" and user_state.get("service") == "mold_remediation" and incoming_type == "chat":
        mold.handle_mold_next(user_id, incoming_body)
        return jsonify({}), 200

    # ───────────────────────────────────────────────────────────────────────
    # (You can add any additional “flow → next” branches here exactly as you had them.)
    # ───────────────────────────────────────────────────────────────────────

    # ───────────────────────────────────────────────────────────────────────
    # 5) If none of the above matched, send a generic fallback.
    # ───────────────────────────────────────────────────────────────────────
    send_text_message(
        user_id,
        "Sorry, I can’t handle that type of message right now.\n"
        "Please tap 'Need help on Pest!' or 'Need help on Mold!' or type 'reset'."
    )
    return jsonify({}), 200


@app.route("/health", methods=["GET"])
def healthcheck():
    return jsonify({"status": "OK"}), 200


if __name__ == "__main__":
    # Optional: if you want to run locally with python dispatcher.py
    app.run(host="0.0.0.0", port=5000, debug=True)
