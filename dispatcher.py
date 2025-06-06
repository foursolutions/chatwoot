# dispatcher.py

from flask import Flask, request, jsonify
import os

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_template_message,
    send_interactive_message
)

app = Flask(__name__)

MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")
print("🔍 MAIN_MENU_TEMPLATE =", MAIN_MENU_TEMPLATE)


@app.route("/verify", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == os.getenv("VERIFY_TOKEN"):
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print("🔍 Received webhook data:", data)

    if "messages" not in data or len(data["messages"]) == 0:
        return jsonify({}), 200

    msg = data["messages"][0]
    chat_id = msg.get("chatId")
    msg_type = msg.get("type")

    print(f"🔍 chat_id = {chat_id}, type = {msg_type}")

    # ─────────────────────────────────────────────────────────────────
    # Normalize incoming_text, including top‐level "body" for type="chat"
    # ─────────────────────────────────────────────────────────────────
    incoming_text = ""
    if msg_type in ("text", "chat", "conversation"):
        # 1MSG sometimes uses top‐level "body" for chat messages
        incoming_text = (
            msg.get("text", {}).get("body", "")
            or msg.get("chat", {}).get("body", "")
            or msg.get("body", "")           # <== look here as well
            or ""
        ).strip().lower()

    elif msg_type == "button_reply":
        incoming_text = msg["button_reply"].get("id", "").strip().lower()

    elif msg_type == "list_reply":
        incoming_text = msg["list_reply"].get("id", "").strip().lower()

    print(f"🔍 incoming_text (normalized) = '{incoming_text}'")


    # ─────────────────────────────────────────────────────────────────
    # 1) If user typed/tapped "reset", clear all flow‐states, send Main Menu
    # ─────────────────────────────────────────────────────────────────
    if incoming_text == "reset":
        print("ℹ️ Reset command detected. Clearing all flow states for:", chat_id)

        clear_user_state("CAR_FUM", chat_id)
        clear_user_state("MOLD",    chat_id)
        clear_user_state("BEDBUG",  chat_id)
        # … clear any other flow prefixes here …

        print("ℹ️ Sending main_menu_v2 template to", chat_id)
        try:
            resp = send_template_message(
                to=chat_id,
                template_name=MAIN_MENU_TEMPLATE,
                template_params=["there"]  # your main_menu_v2 expects 1 placeholder
            )
            print("✅ send_template_message returned:", resp)
        except Exception as e:
            print("❌ send_template_message raised exception:", e)

        return jsonify({}), 200


    # ─────────────────────────────────────────────────────────────────
    # 2) Check active flows and delegate (unchanged from your previous logic)
    # ─────────────────────────────────────────────────────────────────
    state_car  = get_user_state("CAR_FUM", chat_id)
    state_mold = get_user_state("MOLD",   chat_id)
    state_bed  = get_user_state("BEDBUG", chat_id)

    if state_car:
        print(f"🔍 Delegating to Car Fumigation flow (step = {state_car.get('step')})")
        from flows.car_fumigation import handle_car_fumigation_flow
        handle_car_fumigation_flow(chat_id, msg, state_car)
        return jsonify({}), 200

    if state_mold:
        print(f"🔍 Delegating to Mold flow (step = {state_mold.get('step')})")
        from flows.mold import handle_mold_flow
        handle_mold_flow(chat_id, msg, state_mold)
        return jsonify({}), 200

    if state_bed:
        print(f"🔍 Delegating to Bedbug flow (step = {state_bed.get('step')})")
        from flows.bedbug import handle_bedbug_flow
        handle_bedbug_flow(chat_id, msg, state_bed)
        return jsonify({}), 200


    # ─────────────────────────────────────────────────────────────────
    # 3) If no flow is active, check for “start flow” keywords
    # ─────────────────────────────────────────────────────────────────
    if incoming_text == "car_fum":
        print("ℹ️ Starting Car Fumigation flow for", chat_id)
        set_user_state("CAR_FUM", chat_id, {"step": "initial"})
        from flows.car_fumigation import handle_car_fumigation_flow
        handle_car_fumigation_flow(chat_id, msg, {"step": "initial"})
        return jsonify({}), 200

    if incoming_text == "mold":
        print("ℹ️ Starting Mold flow for", chat_id)
        set_user_state("MOLD", chat_id, {"step": "initial"})
        from flows.mold import handle_mold_flow
        handle_mold_flow(chat_id, msg, {"step": "initial"})
        return jsonify({}), 200

    if incoming_text == "bedbug":
        print("ℹ️ Starting Bedbug flow for", chat_id)
        set_user_state("BEDBUG", chat_id, {"step": "initial"})
        from flows.bedbug import handle_bedbug_flow
        handle_bedbug_flow(chat_id, msg, {"step": "initial"})
        return jsonify({}), 200


    # ─────────────────────────────────────────────────────────────────
    # 4) Fallback: re‐send main menu if nothing matched
    # ─────────────────────────────────────────────────────────────────
    print("⚠️ No active flow or command matched; re‐sending main_menu_v2.")
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
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
