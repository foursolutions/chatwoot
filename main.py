import flows.bedbug as bedbug
import flows.mold as mold
import flows.car_fumigation as car_fumigation
import os
import requests
import datetime
import pytz
import re

from flask import Flask, request
from dotenv import load_dotenv

# 1) Load environment variables
load_dotenv()

# 2) Read environment variables
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Your 360dialog API Key or Meta permanent token
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

app = Flask(__name__)

# Global session data dictionaries
live_sessions = {}
car_fumigation_data = {}
mold_removal_data = {}
bedbug_data = {}
last_message_id = {}

# Define admin phone numbers (update with your own admin numbers)
ADMIN_NUMBERS = {"+6587788080"}
# Dynamic mapping: admin number -> target client number.
ADMIN_TARGET = {}

# -------------------------------
# WhatsApp Message Helpers
# -------------------------------

def send_text_message(to, message):
    """
    Send a WhatsApp text message using 360dialog or Meta API.
    """
    url = f"https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"✅ Sent WhatsApp text to {to}: {response.text}")

def send_template_message(to, template_name, namespace, variables):
    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "to": to,
        "type": "template",
        "template": {
            "namespace": namespace,
            "language": {
                "policy": "deterministic",
                "code": "en"
            },
            "name": template_name,
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": var} for var in variables]
                }
            ]
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print("⚠️ Error sending template message:")
        print("Request payload:", payload)
        print("Response text:", response.text)
        fallback_message = f"Hi {variables[0]}, how can I help you today?"
        send_text_message(to, fallback_message)
    else:
        print(f"✅ Sent template message to {to}: {response.text}")

def send_interactive_message(to, payload):
    """
    Send an interactive WhatsApp message using the 360dialog/Meta API.
    (Payload must follow WhatsApp API structure.)
    """
    url = f"https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload["to"] = to  # ensure recipient is correct
    response = requests.post(url, json=payload, headers=headers)
    print(f"✅ Sent interactive message to {to}: {response.text}")

def normalize_number(number):
    """Remove spaces and ensure a leading '+'."""
    number = re.sub(r"\s+", "", number)
    if not number.startswith("+"):
        number = "+" + number
    return number

# -------------------------------
# Live Agent & Menu Functions
# -------------------------------

def initiate_live_agent(to, sender_name):
    live_sessions[to] = True
    text_msg = (
        "Hold on tight—we’re summoning a real, living, breathing, functioning human support agent for you! "
        "They’ll join this chat as soon as they're available. In the meantime, feel free to explore our other services and read our FAQ!"
    )
    send_text_message(to, text_msg)

    if to in mold_removal_data:
        mold.send_mold_removal_faq(
            to, PHONE_NUMBER_ID, ACCESS_TOKEN, send_interactive_message
        )
        final_msg = (
            "Please upload some photos of the affected areas. Wide-angle shots from a doorway or corner help us see the entire space, "
            "allowing our agent to provide a more accurate quote once they review your message."
        )
        send_text_message(to, final_msg)
    elif to in car_fumigation_data:
        car_fumigation.send_car_fumigation_faq(
            to, PHONE_NUMBER_ID, ACCESS_TOKEN, send_interactive_message
        )
    elif to in bedbug_data:
        pass

def end_live_agent_session(to):
    if to in live_sessions:
        del live_sessions[to]
    text_msg = (
        "You have ended the live agent session. Feel free to continue chatting with me for assistance anytime!"
    )
    send_text_message(to, text_msg)

def reset_conversation(to, customer_name):
    car_fumigation_data.pop(to, None)
    mold_removal_data.pop(to, None)
    bedbug_data.pop(to, None)
    live_sessions.pop(to, None)
    send_text_message(to, "Conversation reset. Let's start fresh!")
    send_main_menu(to, customer_name)

def send_main_menu(to, customer_name):
    namespace = "94d66366_9ec1_43a3_a84c_46039bd33ef5"
    template_name = "main_menu"
    send_template_message(to, "main_menu", "94d66366_9ec1_43a3_a84c_46039bd33ef5", [customer_name])

# -------------------------------
# Admin Command Handling
# -------------------------------

def send_admin_command_menu(admin_number):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Admin Commands"},
            "body": {"text": "Select a command:"},
            "footer": {"text": "Admin Options"},
            "action": {
                "button": "Select Command",
                "sections": [
                    {
                        "title": "Master Cmds",
                        "rows": [
                            {
                                "id": "admin_cfum_confirm",
                                "title": "Car Fum Confirm",
                                "description": "Send car fum prep text",
                            },
                            {
                                "id": "admin_mold_confirm",
                                "title": "Mold Rem Confirm",
                                "description": "Send mold prep text",
                            },
                            {
                                "id": "admin_bedbug_confirm",
                                "title": "Bed Bug Confirm",
                                "description": "Send bed bug prep text",
                            },
                            {
                                "id": "admin_payment_methods",
                                "title": "Payment Methods",
                                "description": "Send payment FAQ",
                            },
                            {
                                "id": "admin_reset",
                                "title": "Reset Conversation",
                                "description": "Reset client convo",
                            },
                        ],
                    }
                ],
            },
        },
    }
    send_interactive_message(admin_number, payload)

def handle_admin_text(sender_number, text_body):
    lower_text = text_body.lower()
    if lower_text.startswith("set target"):
        parts = text_body.split()
        if len(parts) == 3:
            target = normalize_number(parts[2])
            ADMIN_TARGET[sender_number] = target
            send_text_message(sender_number, f"Target client set to {target}")
            return True
        else:
            send_text_message(sender_number, "Usage: set target +65XXXXXXXX")
            return True
    elif lower_text == "appointment confirmed":
        target = ADMIN_TARGET.get(sender_number, sender_number)
        car_fumigation.send_car_fumigation_preparation(
            target, PHONE_NUMBER_ID, ACCESS_TOKEN
        )
        send_text_message(
            sender_number, f"Appointment confirmed command sent to {target}"
        )
        return True
    elif lower_text == "commands":
        send_admin_command_menu(sender_number)
        return True
    return False

# -------------------------------
# Flask Webhook Endpoint
# -------------------------------

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        # ADD THE LINE BELOW HERE:
        print("DEBUG - Received verify_token from 360dialog:", verify_token)
        if verify_token == os.environ.get("VERIFY_TOKEN"):
            return challenge, 200
        else:
            return "Verification token mismatch", 403
        
    if request.method == "POST":
        # Only accept Meta/360dialog JSON webhook format
        if not request.is_json:
            print("❌ Unsupported content type:", request.content_type)
            return "Unsupported Media Type", 415

        data = request.get_json()

        try:
            msg = data["entry"][0]["changes"][0]["value"].get("messages", [None])[0]
            if msg is None:
                return "OK", 200

            message_id = msg.get("id")
            sender_number = normalize_number(msg.get("from"))
            sender_name = data["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

            if sender_number in ADMIN_NUMBERS:
                print(f"Admin message from {sender_number}: {msg}")

            # Prevent processing the same message multiple times
            if (
                sender_number in last_message_id
                and last_message_id[sender_number] == message_id
            ):
                return "OK", 200
            last_message_id[sender_number] = message_id

            message_type = msg.get("type")
            text_body = msg["text"]["body"].strip(
            ) if message_type == "text" else ""

            # -------------------------------
            # Bedbug Custom Area Text Input
            # -------------------------------
            if message_type == "text":
                if sender_number in bedbug_data and bedbug_data[sender_number].get(
                    "awaiting_other_area"
                ):
                    bedbug.process_bedbug_text_message(
                        sender_number,
                        text_body,
                        bedbug_data,
                        PHONE_NUMBER_ID,
                        ACCESS_TOKEN,
                        send_text_message,
                    )
                    return "OK", 200

            # Admin text command branch
            if message_type == "text" and sender_number in ADMIN_NUMBERS:
                if handle_admin_text(sender_number, text_body):
                    return "OK", 200

            # Car Fumigation: awaiting vehicle model details
            if sender_number in car_fumigation_data and car_fumigation_data[
                sender_number
            ].get("awaiting_vehicle_model_details"):
                car_fumigation_data[sender_number]["vehicle_details"] = text_body
                car_fumigation_data[sender_number].pop(
                    "awaiting_vehicle_model_details", None
                )
                send_text_message(
                    sender_number, "Vehicle model details noted. Thank you!"
                )
                car_fumigation.send_location_selection(
                    sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                )
                return "OK", 200

            # Car Fumigation pending flows
            if sender_number in car_fumigation_data:
                flow = car_fumigation_data[sender_number]
                if flow.get("awaiting_appointment_datetime"):
                    car_fumigation.handle_appointment_datetime(
                        sender_number, text_body, car_fumigation_data, send_text_message
                    )
                    return "OK", 200
                elif flow.get("awaiting_parking_address"):
                    car_fumigation.handle_parking_address(
                        sender_number, text_body, car_fumigation_data, send_text_message
                    )
                    return "OK", 200
                elif flow.get("awaiting_vehicle_number"):
                    car_fumigation.handle_vehicle_number(
                        sender_number,
                        text_body,
                        car_fumigation_data,
                        send_text_message,
                        PHONE_NUMBER_ID,
                        ACCESS_TOKEN,
                    )
                    return "OK", 200

            # Standard user text handling
            if message_type == "text":
                if text_body.lower() == "reset":
                    reset_conversation(sender_number, sender_name)
                    return "OK", 200
                if text_body.lower() == "end":
                    end_live_agent_session(sender_number)
                    return "OK", 200
                if text_body.lower() in ["live", "live agent", "agent", "connect me"]:
                    initiate_live_agent(sender_number, sender_name)
                    return "OK", 200

                # If user is in a live agent session, do not auto-respond
                if sender_number in live_sessions and live_sessions[sender_number]:
                    print("Live agent session active; auto bot responses are disabled.")
                    return "OK", 200

                # Send main menu
                send_main_menu(sender_number, sender_name)
                print("✅ Sent main menu to", sender_number)
                return "OK", 200

            # Handle interactive messages
            elif message_type == "interactive":
                interactive_data = msg["interactive"]
                # Admin button replies
                if "button_reply" in interactive_data:
                    button_id = interactive_data["button_reply"]["id"]
                    if sender_number in ADMIN_NUMBERS and button_id.startswith(
                        "admin_"
                    ):
                        target = ADMIN_TARGET.get(sender_number, sender_number)
                        if button_id == "admin_cfum_confirm":
                            car_fumigation.send_car_fumigation_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif button_id == "admin_mold_confirm":
                            mold.send_mold_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif button_id == "admin_bedbug_confirm":
                            bedbug.process_bedbug_faq_response(
                                target,
                                "bbfaq_preparation",
                                PHONE_NUMBER_ID,
                                ACCESS_TOKEN,
                                send_text_message,
                            )
                        elif button_id == "admin_payment_methods":
                            send_text_message(
                                target,
                                "We accept the following payment methods:\n"
                                "* PayNow: Payment via UEN: 201812722M\n"
                                "* Atome: Interest-free installment payments (3 months). A 5% surcharge applies.\n"
                                "* Cash: If other options aren't feasible, inform us in advance and kindly prepare the exact amount.",
                            )
                        elif button_id == "admin_reset":
                            reset_conversation(target, "Client")

                        send_text_message(
                            sender_number, "Admin command executed.")
                        return "OK", 200

                # Admin list replies
                if "list_reply" in interactive_data:
                    list_id = interactive_data["list_reply"]["id"]
                    if sender_number in ADMIN_NUMBERS and list_id.startswith("admin_"):
                        target = ADMIN_TARGET.get(sender_number, sender_number)
                        if list_id == "admin_cfum_confirm":
                            car_fumigation.send_car_fumigation_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif list_id == "admin_mold_confirm":
                            mold.send_mold_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif list_id == "admin_bedbug_confirm":
                            bedbug.process_bedbug_faq_response(
                                target,
                                "bbfaq_preparation",
                                PHONE_NUMBER_ID,
                                ACCESS_TOKEN,
                                send_text_message,
                            )
                        elif list_id == "admin_payment_methods":
                            send_text_message(
                                target,
                                "We accept the following payment methods:\n"
                                "* PayNow: Payment via UEN: 201812722M\n"
                                "* Atome: Interest-free installment payments (3 months). A 5% surcharge applies.\n"
                                "* Cash: If other options aren't feasible, inform us in advance and kindly prepare the exact amount.",
                            )
                        elif list_id == "admin_reset":
                            reset_conversation(target, "Client")

                        send_text_message(
                            sender_number, "Admin command executed.")
                        return "OK", 200

                # Normal user interactive flows (use your dispatcher/flows as in original)
                # -- [Your original button/list handling logic for flows continues below] --
                # (For brevity, refer to your original code for the rest)
                # If you want, I can expand this area in full in the next step.

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

