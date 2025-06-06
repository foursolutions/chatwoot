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

# The name of your “main menu” template (e.g. "main_menu_v2")
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")
print("🔍 MAIN_MENU_TEMPLATE =", MAIN_MENU_TEMPLATE)


@app.route("/verify", methods=["GET"])
def verify():
    """
    1MSG will request:
      GET /verify?hub.verify_token=<VERIFY_TOKEN>&hub.challenge=<challenge>
    We must respond with hub.challenge if the verify_token matches.
    """
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == os.getenv("VERIFY_TOKEN"):
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Receives incoming 1MSG messages. 1MSG sends JSON like:

    {
      "messages": [
        {
          "chatId": "6591234567@c.us",
          "type": "text" | "button" | "button_reply" | "list_reply" | "chat" | ...,
          "body": "hello",                         # for type "chat" or "button"
          "text": { "body": "hello" },             # for type "text"
          "button_reply": { "id": "btn_id", ... }, # for type "button_reply"
          "list_reply":   { "id": "row_id", ... }  # for type "list_reply"
          ...
        }
      ]
    }
    """
    data = request.get_json(force=True)
    print("🔍 Received webhook data:", data)

    # If no "messages" or empty, return 200 immediately
    if "messages" not in data or len(data["messages"]) == 0:
        return jsonify({}), 200

    msg = data["messages"][0]
    chat_id = msg.get("chatId")   # e.g. "6587788080@c.us"
    msg_type = msg.get("type")    # "text", "chat", "button", "button_reply", "list_reply", etc.

    print(f"🔍 chat_id = {chat_id}, type = {msg_type}")

    # ─────────────────────────────────────────────────────────────────
    # Normalize incoming_text across payload types
    # ─────────────────────────────────────────────────────────────────
    incoming_text = ""

    if msg_type in ("text", "chat", "conversation"):
        # 1MSG sometimes uses top-level "body", or nested "text" / "chat" with "body"
        incoming_text = (
            msg.get("text", {}).get("body", "")
            or msg.get("chat", {}).get("body", "")
            or msg.get("body", "")      # top-level "body"
            or ""
        ).strip().lower()

    elif msg_type == "button":
        # 1MSG returns type="button" with body = the quick-reply text
        incoming_text = msg.get("body", "").strip().lower()

    elif msg_type == "button_reply":
        # Some flows might explicitly return a "button_reply" object
        incoming_text = msg["button_reply"].get("id", "").strip().lower()

    elif msg_type == "list_reply":
        incoming_text = msg["list_reply"].get("id", "").strip().lower()

    print(f"🔍 incoming_text (normalized) = '{incoming_text}'")


    # ─────────────────────────────────────────────────────────────────
    # 1) If user typed/tapped "reset", clear all flow-states and re-send Main Menu
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
                template_params=["there"]   # must be non-empty to satisfy {{1}}
            )
            print("✅ send_template_message returned:", resp)
        except Exception as e:
            print("❌ send_template_message raised exception:", e)

        return jsonify({}), 200


    # ─────────────────────────────────────────────────────────────────
    # 2) If user is already mid-flow, delegate to that flow’s handler
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
    # 3) No flow is active, so check “start-flow” button labels / keywords
    # ─────────────────────────────────────────────────────────────────
    if incoming_text == "need help on pest!":
        print("ℹ️ Starting Car Fumigation flow for", chat_id)
        set_user_state("CAR_FUM", chat_id, {"step": "initial"})
        from flows.car_fumigation import handle_car_fumigation_flow
        handle_car_fumigation_flow(chat_id, msg, {"step": "initial"})
        return jsonify({}), 200

    if incoming_text in ("need help on mold!", "mold"):
        print("ℹ️ Starting Mold flow for", chat_id)
        set_user_state("MOLD", chat_id, {"step": "initial"})
        from flows.mold import handle_mold_flow
        handle_mold_flow(chat_id, msg, {"step": "initial"})
        return jsonify({}), 200

    if incoming_text in ("need help on bedbug!", "bedbug"):
        print("ℹ️ Starting Bedbug flow for", chat_id)
        set_user_state("BEDBUG", chat_id, {"step": "initial"})
        from flows.bedbug import handle_bedbug_flow
        handle_bedbug_flow(chat_id, msg, {"step": "initial"})
        return jsonify({}), 200


    # ─────────────────────────────────────────────────────────────────
    # 4) Nothing matched → re-send main_menu_v2 template
    # ─────────────────────────────────────────────────────────────────
    print("⚠️ No active flow or command matched; re‐sending main_menu_v2.")
    try:
        send_template_message(
            to=chat_id,
            template_name=MAIN_MENU_TEMPLATE,
            template_params=["there"]
        )
    except Exception as e:
        print("❌ Error re‐sending main_menu_v2:", e)

    return jsonify({}), 200


if __name__ == "__main__":
    # For local debugging; Heroku uses gunicorn in production.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
