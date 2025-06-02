# main.py

import os
import requests
import datetime
import pytz
import re

from flask import Flask, request
from dotenv import load_dotenv

import dispatcher  # your dispatcher.py
from flows.car_fumigation import send_pest_control_dropdown, send_car_fum_menu

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
ACCESS_TOKEN    = os.getenv("WHATSAPP_TOKEN")    # 360dialog API Key
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")

app = Flask(__name__)

# Used to dedupe incoming WhatsApp messages
last_message_id = {}

# -------------------------------
# Helper: Normalize incoming number
# -------------------------------
def normalize_number(number):
    number = re.sub(r"\s+", "", number)
    if not number.startswith("+"):
        number = "+" + number
    return number

# -------------------------------
# WhatsApp Text / Template Senders
# -------------------------------
def send_text_message(to, message):
    """
    Send a plain text message via 360dialog.
    """
    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    r = requests.post(url, json=payload, headers=headers)
    print(f"✅ Sent WhatsApp text to {to}: {r.text}")

def send_template_message(to, template_name, namespace, variables):
    """
    Send a template message via 360dialog v2 API.
    """
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "namespace": namespace,
            "language": {"policy": "deterministic", "code": "en"},
            "name": template_name,
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(var)} for var in variables]
                }
            ]
        }
    }
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code != 200:
        print("⚠️ Error sending template message:")
        print("Request payload:", payload)
        print("Response text:", r.text)
    else:
        print(f"✅ Sent template '{template_name}' → {to}: {r.text}")

def send_interactive_message(to, payload):
    """
    Send a raw interactive (list/button) payload via 360dialog.
    """
    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload["to"] = to
    payload["messaging_product"] = "whatsapp"
    r = requests.post(url, json=payload, headers=headers)
    print(f"✅ Sent interactive message to {to}: {r.text}")

# -------------------------------
# Main Menu and Live-Agent
# -------------------------------
def send_main_menu(to, customer_name):
    """
    Sends your approved 'main_menu_v2' template.
    Assumes you have set up a template named 'main_menu_v2'
    under namespace '94d66366_9ec1_43a3_a84c_46039bd33ef5'.
    The template's body should use one placeholder for the customer's name.
    """
    namespace     = "94d66366_9ec1_43a3_a84c_46039bd33ef5"
    template_name = "main_menu_v2"
    send_template_message(to, template_name, namespace, [customer_name])

def initiate_live_agent(to, sender_name):
    """
    Escalate to a live agent.
    """
    text_msg = (
        "Hold on tight—we’re summoning a real, living, breathing, functioning human support agent for you! "
        "They’ll join this chat as soon as they're available. In the meantime, feel free to explore our services or read our FAQ!"
    )
    send_text_message(to, text_msg)

def reset_conversation(to, customer_name):
    send_text_message(to, "Conversation reset. Let's start fresh!")
    send_main_menu(to, customer_name)

# -------------------------------
# Admin placeholders
# -------------------------------
ADMIN_NUMBERS = {"+6587788080"}
ADMIN_TARGET  = {}

def handle_admin_text(sender_number, text_body):
    """
    Admin text commands.
    """
    lower = text_body.lower()
    if lower.startswith("set target"):
        parts = text_body.split()
        if len(parts) == 3:
            target = normalize_number(parts[2])
            ADMIN_TARGET[sender_number] = target
            send_text_message(sender_number, f"Target client set to {target}")
            return True
        else:
            send_text_message(sender_number, "Usage: set target +65XXXXXXXX")
            return True

    if lower == "appointment confirmed":
        target = ADMIN_TARGET.get(sender_number, sender_number)
        from flows.car_fumigation import send_car_fumigation_preparation
        send_car_fumigation_preparation(target, PHONE_NUMBER_ID, ACCESS_TOKEN)
        send_text_message(sender_number, f"Appointment confirmed command sent to {target}")
        return True

    if lower == "commands":
        send_text_message(sender_number, "Admin commands: set target +65..., appointment confirmed, commands")
        return True

    return False

# -------------------------------
# Flask Webhook Endpoint
# -------------------------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # --- VERIFY (GET) ---
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge    = request.args.get("hub.challenge")
        print("DEBUG – Received verify_token:", verify_token)
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        return "Verification token mismatch", 403

    # --- INBOUND MESSAGE (POST) ---
    if not request.is_json:
        print("❌ Unsupported content type:", request.content_type)
        return "Unsupported Media Type", 415

    data = request.get_json()
    try:
        msg = data["entry"][0]["changes"][0]["value"].get("messages", [None])[0]
        if msg is None:
            return "OK", 200

        message_id    = msg.get("id")
        sender_number = normalize_number(msg.get("from"))
        sender_name   = data["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

        # Prevent duplicate processing
        if sender_number in last_message_id and last_message_id[sender_number] == message_id:
            return "OK", 200
        last_message_id[sender_number] = message_id

        message_type = msg.get("type")
        text_body    = ""
        button_reply = None
        list_reply   = None

        if message_type == "text":
            text_body = msg["text"]["body"].strip()

            # --- ADMIN TEXT? ---
            if sender_number in ADMIN_NUMBERS:
                if handle_admin_text(sender_number, text_body):
                    return "OK", 200

            # --- ANY FREE-TEXT → SHOW MAIN MENU ---
            send_main_menu(sender_number, sender_name)
            return "OK", 200

        elif message_type == "interactive":
            interactive_data = msg["interactive"]

            # Extract button‐reply text or list‐reply title
            if "button_reply" in interactive_data:
                button_reply = interactive_data["button_reply"]["text"]
            if "list_reply" in interactive_data:
                list_reply = interactive_data["list_reply"]["title"]

            # --- ADMIN INTERACTIVE? ---
            if sender_number in ADMIN_NUMBERS and button_reply and button_reply.startswith("admin_"):
                send_text_message(sender_number, "Admin command executed.")
                return "OK", 200

            # --- TOP‐LEVEL MENU INTERACTIVE ---
            if button_reply == "Need help on Pest!":
                # Show the full Pest Control dropdown (Car Fumigation, Bed Bugs, etc.)
                send_pest_control_dropdown(sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN)

                # Seed Redis state for selecting a specific service
                import json
                from dispatcher import FLOW, r as REDIS_CONN
                REDIS_CONN.delete(f"{FLOW}:{sender_number}")
                REDIS_CONN.set(f"{FLOW}:{sender_number}", json.dumps({"step": "select_service"}), ex=3600)
                return "OK", 200

            if button_reply == "Live Human":
                initiate_live_agent(sender_number, sender_name)
                return "OK", 200

            if button_reply == "Need help on Mold!":
                send_text_message(sender_number, "Sorry, Mold removal flow is coming soon—please check back later.")
                return "OK", 200

            # --- OTHERWISE → Pass to dispatcher (pest-control scope) ---
            dispatcher.handle_message(
                sender_number,
                message_text="",
                button_reply=button_reply,
                list_reply=list_reply,
                access_token=ACCESS_TOKEN
            )
            return "OK", 200

    except KeyError as e:
        print("ℹ️ No message found, skipping...", e)
        return "OK", 200
    except Exception as ex:
        print("❌ Error in webhook processing:", ex)
        return "OK", 200

    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Four Solutions Chatbot is live!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

