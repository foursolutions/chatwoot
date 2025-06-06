# dispatcher.py
from flask import Flask, request, jsonify
import os
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_template_message,
    send_list_message
)

app = Flask(__name__)

# Load the name of your main menu template from ENV (e.g. "main_menu_v2")
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")
print("🔍 MAIN_MENU_TEMPLATE =", MAIN_MENU_TEMPLATE)


@app.route("/verify", methods=["GET"])
def verify():
    """
    Verification endpoint for 1msg webhook setup:
    1msg will GET /verify?hub.verify_token=<VERIFY_TOKEN>&hub.challenge=<challenge>
    Respond with hub.challenge if token matches.
    """
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == os.getenv("VERIFY_TOKEN"):
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Main webhook endpoint to receive incoming 1msg messages.
    """
    data = request.get_json(force=True)

    # ─── DEBUGGING: print the entire payload so we know its exact structure ───
    print("🔍 Received webhook data:", data)

    # Basic guard: if no messages key or empty, just return 200 OK
    if "messages" not in data or len(data["messages"]) == 0:
        return jsonify({}), 200

    msg = data["messages"][0]
    chat_id = msg.get("chatId")  # e.g. "6589123456@c.us"
    msg_type = msg.get("type")   # e.g. "chat", "text", "list_reply", or "button_reply"

    # ─── DEBUGGING: print chat_id & msg_type ───
    print(f"🔍 chat_id = {chat_id}, type = {msg_type}")

    # Extract incoming_text for "chat" or "text" or "button_reply" or "list_reply"
    incoming_text = ""
    if msg_type in ("text", "chat", "conversation"):
        # In many 1msg setups, the text they send comes as type "chat"
        incoming_text = msg.get("text", {}).get("body", "").strip().lower()
    elif msg_type == "button_reply":
        incoming_text = msg["button_reply"].get("id", "").strip().lower()
    elif msg_type == "list_reply":
        incoming_text = msg["list_reply"].get("id", "").strip().lower()

    # ─── DEBUGGING: print the normalized incoming_text ───
    print(f"🔍 incoming_text (after strip/lower) = '{incoming_text}'")

    # ─── 1. If user typed or tapped "reset", clear all flows and send main menu ───
    if incoming_text == "reset":
        print("ℹ️ We are in the reset branch now.")

        # Clear state for each flow prefix you use
        clear_user_state("CAR_FUM", chat_id)
        clear_user_state("MOLD", chat_id)
        clear_user_state("BEDBUG", chat_id)
        # … add any other flow prefixes here …

        print("ℹ️ Sending main_menu_v2 template to", chat_id)
        try:
            # NOTE: main_menu_v2 expects exactly 1 placeholder. We’ll pass an empty string.
            resp = send_template_message(
                to=chat_id,
                template_name=MAIN_MENU_TEMPLATE,
                template_params=[""]
            )
            print("✅ send_template_message returned:", resp)
        except Exception as e:
            print("❌ send_template_message raised an exception:", e)

        return jsonify({}), 200

    # ─── 2. Otherwise, route into the correct flow based on user_state or button ID ─┛
    current_flow = get_user_state("CURRENT_FLOW", chat_id).get("flow_name")
    print("🔍 CURRENT_FLOW for this user:", current_flow)

    # If user is in Car Fumigation flow, delegate to that handler
    if current_flow == "CAR_FUM":
        from flows.car_fumigation import handle_car_fumigation_flow
        handle_car_fumigation_flow(chat_id, msg)
        return jsonify({}), 200

    # If user is in Mold flow, delegate to that handler (example)
    if current_flow == "MOLD":
        from flows.mold import handle_mold_flow
        handle_mold_flow(chat_id, msg)
        return jsonify({}), 200

    # If user is in Bedbug flow, delegate (example)
    if current_flow == "BEDBUG":
        from flows.bedbug import handle_bedbug_flow
        handle_bedbug_flow(chat_id, msg)
        return jsonify({}), 200

    # ─── 3. If no state yet, interpret incoming_text as “pick a flow” from main menu ───
    # e.g. If your main_menu_v2 template’s buttons/quick‐reply IDs are "car_fum", "mold", "bedbug"
    if incoming_text == "car_fum":
        set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "CAR_FUM"})
        from flows.car_fumigation import handle_car_fumigation_flow
        handle_car_fumigation_flow(chat_id, msg)
        return jsonify({}), 200

    if incoming_text == "mold":
        set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "MOLD"})
        from flows.mold import handle_mold_flow
        handle_mold_flow(chat_id, msg)
        return jsonify({}), 200

    if incoming_text == "bedbug":
        set_user_state("CURRENT_FLOW", chat_id, {"flow_name": "BEDBUG"})
        from flows.bedbug import handle_bedbug_flow
        handle_bedbug_flow(chat_id, msg)
        return jsonify({}), 200

    # ─── 4. If nothing matched, re‐send main menu template ──────────────────────────
    print("⚠️ No flow matched; re‐sending main_menu_v2.")
    try:
        send_template_message(
            to=chat_id,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=[""]
        )
    except Exception as e:
        print("❌ Error re‐sending main_menu_v2:", e)
    return jsonify({}), 200


if __name__ == "__main__":
    # For local testing; Heroku will run via gunicorn in production.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
