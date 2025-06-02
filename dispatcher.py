import os
import json
from flask import Flask, request, make_response
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_interactive_message,
    send_text_message,
)
from flows import car_fumigation  # Car Fumigation flow

app = Flask(__name__)

# ------------------------------------------------------------------------------
#  Environment variables (must be set in Heroku config vars)
# ------------------------------------------------------------------------------
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")       # Your webhook verification token
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID") # Used by send_* functions as needed

# Redis key prefix for Car Fumigation user states
REDIS_PREFIX = "carfum"

# Name of the “echo” fallback template (approved in 360dialog)
ECHO_TEMPLATE = "echo_message_text"


# ------------------------------------------------------------------------------
#  Webhook Verification (GET)
# ------------------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Webhook verification endpoint. Meta/WhatsApp will call this with:
      - hub.mode
      - hub.verify_token
      - hub.challenge
    We must echo back the “hub.challenge” if the token matches VERIFY_TOKEN.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return make_response(challenge, 200)
    else:
        return make_response("Verification token mismatch", 403)


# ------------------------------------------------------------------------------
#  Main Webhook Handler (POST)
# ------------------------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Handle incoming WhatsApp messages sent via 360dialog:
      - Text messages
      - Interactive replies (list or quick‐reply button)
      - Other types (we fallback if unsupported)
    We delegate Car Fumigation logic to flows/car_fumigation.handle_car_fumigation_flow.
    """
    payload = request.get_json()

    try:
        # Drill down into the WhatsApp payload structure:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        # If there are no messages, just return 200
        if not messages:
            return make_response("No messages to process", 200)

        message = messages[0]
        from_number = message["from"]    # e.g. "6581234567"
        msg_type = message.get("type")   # "text", "interactive", "button", etc.

        # 1) If it's a plain text message:
        if msg_type == "text":
            text_body = message["text"]["body"].strip().lower()
            print(f"[DEBUG] Received TEXT from {from_number}: '{text_body}'")

            # If user types "reset" → clear state and send main menu
            if text_body == "reset":
                print(f"[DEBUG] 'reset' detected for {from_number}. Clearing state and sending main menu.")
                clear_user_state(REDIS_PREFIX, from_number)
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Reset: Main menu sent", 200)

            # Fetch any existing user state from Redis
            state = get_user_state(REDIS_PREFIX, from_number)
            current_step = state.get("step")

            # If user typed "menu" or there is no existing state → send main menu
            if text_body == "menu" or not current_step:
                print(f"[DEBUG] Sending main menu to {from_number} (text_body='{text_body}', current_step={current_step})")
                clear_user_state(REDIS_PREFIX, from_number)
                car_fumigation.send_main_menu(
                    to=from_number,
                    phone_number_id=PHONE_NUMBER_ID
                )
                return make_response("Main menu sent", 200)

            # If we do have a state, delegate to Car Fumigation flow
            if state:
                print(f"[DEBUG] Delegating to handle_car_fumigation_flow for {from_number}, step={current_step}")
                car_fumigation.handle_car_fumigation_flow(
                    from_number=from_number,
                    message=message,
                    user_state=state
                )
                return make_response("Flow step handled", 200)

            # No valid state and not "menu" or "reset" → catch-all fallback
            catchall_text = (
                "Sorry, I didn’t understand that. "
                "Please tap 'Need help on Pest!' or type 'menu' to see options again."
            )
            print(f"[DEBUG] No state & unrecognized text for {from_number}: '{text_body}'. Sending fallback.")
            send_template_message(
                to=from_number,
                template_name=ECHO_TEMPLATE,
                template_params=[catchall_text]
            )
            return make_response("Echo fallback sent", 200)

        # 2) If it's an interactive list reply (msg_type == "interactive"):
        elif msg_type == "interactive":
            print(f"[DEBUG] Received INTERACTIVE payload from {from_number}: {json.dumps(message)}")
            state = get_user_state(REDIS_PREFIX, from_number)
            car_fumigation.handle_car_fumigation_flow(
                from_number=from_number,
                message=message,
                user_state=state
            )
            return make_response("Interactive reply handled", 200)

        # 3) If it's a quick‐reply button (msg_type == "button"):
        elif msg_type == "button":
            print(f"[DEBUG] Received BUTTON payload from {from_number}: {json.dumps(message)}")
            state = get_user_state(REDIS_PREFIX, from_number)
            car_fumigation.handle_car_fumigation_flow(
                from_number=from_number,
                message=message,
                user_state=state
            )
            return make_response("Button reply handled", 200)

        # 4) Any other message types (media, etc.) → send fallback
        else:
            catchall_text = (
                "Sorry, I can’t handle that type of message. "
                "Please tap 'Need help on Pest!' or type 'menu'."
            )
            print(f"[DEBUG] Received unsupported msg_type='{msg_type}' from {from_number}. Sending fallback.")
            send_template_message(
                to=from_number,
                template_name=ECHO_TEMPLATE,
                template_params=[catchall_text]
            )
            return make_response("Unsupported message type fallback sent", 200)

    except Exception as e:
        print(f"Error in receive_message: {e}")
        return make_response("Error processing message", 200)


# ------------------------------------------------------------------------------
#  Run the Flask app
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
