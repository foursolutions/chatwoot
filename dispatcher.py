# dispatcher.py

import os
import json
import traceback
from flask import Flask, request, Response

# Import our helper functions (no circular import here!)
from helpers import (
    send_text_message,
    send_template_message,
    get_user_state,
    set_user_state,
    clear_user_state
)

# Import each of your flow‐handlers.  We assume you have a "flows" folder
# alongside dispatcher.py with files like car_fumigation.py, mold.py, etc.
from flows.car_fumigation import handle_car_fumigation_flow
from flows.mold import handle_mold_flow
from flows.bedbug import handle_bedbug_flow

app = Flask(__name__)

# ---------------------------------------------------------
# Load environment variables at startup
# ---------------------------------------------------------
VERIFY_TOKEN        = os.environ.get("VERIFY_TOKEN", "")
API_KEY             = os.environ.get("1MSG_API_KEY", "")
BASE_URL            = os.environ.get("1MSG_BASE_URL", "").rstrip("/")
LANG_CODE           = os.environ.get("1MSG_LANG_CODE", "en")
MAIN_MENU_TEMPLATE  = os.environ.get("MAIN_MENU_TEMPLATE", "main_menu_v2")
# If you need per‐flow template names, you can add them here as well:
#   CAR_MENU_TEMPLATE  = os.environ.get("CAR_MENU_TEMPLATE", "car_fum_menu")
#   MOLD_MENU_TEMPLATE = os.environ.get("MOLD_MENU_TEMPLATE", "mold_menu")
#   etc.


# ---------------------------------------------------------
# Webhook endpoint (1MSG → your Flask app)
# ---------------------------------------------------------
@app.route("/webhook", methods=["GET", "POST"])
def receive_message():
    # For GET verification (if 1MSG ever does webhook verification via query params)
    if request.method == "GET":
        token = request.args.get("hub.verify_token", "")
        challenge = request.args.get("hub.challenge", "")
        if token == VERIFY_TOKEN:
            return Response(challenge, status=200)
        else:
            return Response("Invalid verify token", status=403)

    # For POST (actual incoming messages)
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return Response("Bad Request: payload is not JSON", status=400)

    # Debug/log the raw JSON we received:
    print(">>>> RAW INCOMING JSON:", json.dumps(payload))

    # 1MSG sends incoming messages under payload["messages"] as a list.
    # We'll just look at the first message in the list.
    if "messages" in payload and isinstance(payload["messages"], list) and len(payload["messages"]) > 0:
        msg = payload["messages"][0]

        from_number = msg.get("author") or msg.get("from")  # e.g. "6587788080@c.us"
        # Strip off the "@c.us"
        if from_number.endswith("@c.us"):
            from_number = from_number.replace("@c.us", "")
        elif from_number.endswith("@g.us"):
            from_number = from_number.replace("@g.us", "")

        msg_type = msg.get("type")
        # -------------------------------------------------
        # CASE A: Plain chat text
        # -------------------------------------------------
        if msg_type == "chat":
            text = msg.get("body", "").strip().lower()
            # If user says "reset", clear state and show the main menu again:
            if text == "reset":
                clear_user_state("car", from_number)
                # Show main menu
                # We arbitrarily pass a dummy "body parameter" of "there" so that the template engine can fill its {{1}}.
                send_template_message(
                    to=from_number,
                    token=API_KEY,
                    template_name=MAIN_MENU_TEMPLATE,
                    language={"policy": "deterministic", "code": LANG_CODE},
                    params=[
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": "there"}
                            ]
                        }
                    ]
                )
                return Response(status=200)

            # Otherwise, drop into the car_fumigation flow first (since "car" is our default flow).
            # If you have a top‐level dispatcher that routes to multiple flows,
            # you can examine text or user state here to decide which "flow" to call.
            try:
                return handle_car_fumigation_flow(from_number, msg, API_KEY, BASE_URL)
            except Exception:
                traceback.print_exc()
                return Response(status=500)

        # -------------------------------------------------
        # CASE B: Button‐press (interactive button)
        # -------------------------------------------------
        elif msg_type == "button":
            # A button click always has msg["body"] == the payload/text of that button,
            # and msg["quotedMsgId"] matches the original template’s ID.
            # We pass it along to the same flow‐handler so it can examine it.
            try:
                return handle_car_fumigation_flow(from_number, msg, API_KEY, BASE_URL)
            except Exception:
                traceback.print_exc()
                return Response(status=500)

        # -------------------------------------------------
        # CASE C: Other message types (e.g. media, template ack, etc.)
        # -------------------------------------------------
        else:
            # You could handle other types here (e.g. "image", "document", etc.).
            return Response(status=200)

    # If we get here, payload didn’t match what we expect:
    return Response(status=200)


if __name__ == "__main__":
    # Only for local testing; on Heroku we let gunicorn handle the server.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
