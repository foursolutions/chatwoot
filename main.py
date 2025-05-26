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
from twilio.rest import Client

# 1) Load environment variables
load_dotenv()

# 2) Read environment variables
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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
# Helper Functions
# -------------------------------

def normalize_number(number):
    """Remove spaces and ensure a leading '+'."""
    number = re.sub(r"\s+", "", number)
    if not number.startswith("+"):
        number = "+" + number
    return number

def send_text_message(to_number, message):
    """
    Send a WhatsApp message using Twilio.
    """
    try:
        msg = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
            body=message
        )
        print(f"✅ Sent Twilio WhatsApp message to {to_number}. SID: {msg.sid}")
    except Exception as e:
        print(f"❌ Failed to send WhatsApp message via Twilio: {e}")

def send_interactive_message(to, payload):
    # Placeholder for interactive messages - Twilio currently doesn't support
    # Facebook Graph API calls here. You can implement Twilio interactive messages later.
    print(f"[Interactive message placeholder] To: {to}, Payload: {payload}")

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
    tz = pytz.timezone("Asia/Singapore")
    now = datetime.datetime.now(tz)
    hour = now.hour
    if hour < 4:
        greeting = (
            "Now it might be too late for the mortal body to be awake, but I am here to help! "
            "If there's an emergency, please call us!"
        )
    elif hour < 8:
        greeting = (
            "The human controlling me might not be awake yet, but I am here to help!"
        )
    elif hour < 12:
        greeting = "Good morning!"
    elif hour < 18:
        greeting = "Afternoon!"
    else:
        greeting = "Evening!"

    welcome_message = (
        f"{greeting} {customer_name}, thanks for reaching out to Four Solutions! I'm Solvia, your fun and friendly chatbot. "
        "How may I help you today? (Tap 'Live Human' anytime for immediate support, or choose one of the options below.)"
    )
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": welcome_message},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": "pest_control", "title": "Need help on Pest!"},
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "mold_removal", "title": "Need help on Mold!"},
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "real_human", "title": "Live Human"},
                    },
                ]
            },
        },
    }
    send_interactive_message(to, payload)

# -------------------------------
# Admin Command Handling (Dynamic Target)
# -------------------------------

def send_admin_command_menu(admin_number):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": admin_number,
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

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification token mismatch", 403

    if request.method == "POST":
        data = None
        # Accept both JSON (Meta) and form (Twilio)
        if request.is_json:
            data = request.get_json()
        elif request.content_type and request.content_type.startswith("application/x-www-form-urlencoded"):
            data = request.form.to_dict()
            print("⚠️ Received form-encoded data:", data)
            # Map Twilio format to WhatsApp-like structure
            data = {
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "id": data.get("MessageSid"),
                                "from": data.get("From", "").replace("whatsapp:", ""),
                                "type": "text",
                                "text": {"body": data.get("Body", "")},
                            }],
                            "contacts": [{
                                "profile": {"name": data.get("ProfileName", "")}
                            }]
                        }
                    }]
                }]
            }
        else:
            print("❌ Unsupported content type:", request.content_type)
            return "Unsupported Media Type", 415

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
            # Check for Bedbug Custom Area Text Input
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

            # Check if user is awaiting vehicle model details input (Car Fumigation)
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

            # Check if user is in a pending car fumigation appointment flow
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

            # Handle non-admin text messages
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

                # Send main menu instead of test reply
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

                        # Admin button logic for Car Fum, Mold, Payment, Reset
                        if button_id == "admin_cfum_confirm":
                            car_fumigation.send_car_fumigation_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif button_id == "admin_mold_confirm":
                            mold.send_mold_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif button_id == "admin_bedbug_confirm":
                            # NEW: Send bed bug "prep" text by calling bedbug FAQ for 'bbfaq_preparation'
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

                        # Admin list logic for Car Fum, Mold, Payment, Reset
                        if list_id == "admin_cfum_confirm":
                            car_fumigation.send_car_fumigation_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif list_id == "admin_mold_confirm":
                            mold.send_mold_preparation(
                                target, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        elif list_id == "admin_bedbug_confirm":
                            # NEW: Send bed bug "prep" text by calling bedbug FAQ for 'bbfaq_preparation'
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

                # Normal user interactive flows
                if "button_reply" in interactive_data:
                    button_id = interactive_data["button_reply"]["id"]

                    # Main Menu Options
                    if button_id == "pest_control":
                        car_fumigation.send_pest_control_dropdown(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif button_id == "mold_removal":
                        mold.send_mold_option_prompt(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif button_id == "real_human":
                        initiate_live_agent(sender_number, sender_name)
                    elif button_id == "return_main_menu":
                        send_main_menu(sender_number, sender_name)

                    # Car Fumigation Flow
                    elif button_id == "car_fum_quote":
                        car_fumigation.send_car_fumigation_followup(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif button_id in ["luxury_yes", "luxury_no"]:
                        car_fumigation_data.setdefault(sender_number, {})[
                            "continental"
                        ] = button_id
                        car_fumigation.send_location_selection(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif button_id == "book_appointment":
                        car_fumigation.send_appointment_method_prompt(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif button_id == "apt_asap":
                        car_fumigation_data.setdefault(sender_number, {})[
                            "appointment_datetime"
                        ] = "ASAP"
                        send_text_message(
                            sender_number,
                            "Please provide your full parking address (where the vehicle will be).",
                        )
                        car_fumigation_data[sender_number][
                            "awaiting_parking_address"
                        ] = True
                    elif button_id == "apt_enter_datetime":
                        send_text_message(
                            sender_number,
                            "Please enter your preferred date and time for the appointment.",
                        )
                        car_fumigation_data.setdefault(sender_number, {})[
                            "awaiting_appointment_datetime"
                        ] = True
                    elif button_id == "confirm_apt_yes":
                        initiate_live_agent(sender_number, sender_name)
                    elif button_id == "confirm_apt_no":
                        send_text_message(
                            sender_number,
                            "Let's update your appointment details. You can type your preferred date and time again.",
                        )
                        car_fumigation_data[sender_number][
                            "awaiting_appointment_datetime"
                        ] = True
                    elif button_id == "fumigation_faq":
                        car_fumigation.send_car_fumigation_faq(
                            sender_number,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_interactive_message,
                        )

                    # Bedbug Flow
                    elif button_id == "bedbug_quote":
                        bedbug_data[sender_number] = {}
                        bedbug.send_bedbug_area_selection(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN, bedbug_data
                        )
                    elif button_id == "bedbug_more_info":
                        bedbug.send_bedbug_faq_list(
                            sender_number,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_interactive_message,
                        )
                    elif button_id == "bedbug_add_area_yes":
                        bedbug.process_bedbug_area_add_confirmation(
                            sender_number,
                            "bedbug_add_area_yes",
                            bedbug_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif button_id == "bedbug_add_area_no":
                        bedbug.process_bedbug_area_add_confirmation(
                            sender_number,
                            "bedbug_add_area_no",
                            bedbug_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif button_id == "bedbug_confirm_yes":
                        bedbug.process_bedbug_confirmation(
                            sender_number,
                            "bedbug_confirm_yes",
                            bedbug_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                            initiate_live_agent,
                            sender_name,
                            send_interactive_message=send_interactive_message,
                        )
                    elif button_id == "bedbug_confirm_no":
                        bedbug.process_bedbug_confirmation(
                            sender_number,
                            "bedbug_confirm_no",
                            bedbug_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                            None,
                            None,
                        )

                    # Mold Flow
                    elif button_id == "mold_get_quote":
                        mold.new_mold_quote_flow_start(
                            sender_number,
                            mold_removal_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                        )
                    elif button_id == "mold_more_info":
                        mold.send_mold_removal_faq(
                            sender_number,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_interactive_message,
                        )
                    elif button_id == "mold_confirm_yes":
                        areas = mold_removal_data.get(sender_number, {}).get(
                            "affected_areas", []
                        )
                        if "Entire Unit" in areas:
                            mold.send_entire_unit_inspection_prompt(
                                sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                            )
                        else:
                            send_text_message(
                                sender_number,
                                "Thanks for providing the above details. A live human agent will be coming to assist you shortly.",
                            )
                            initiate_live_agent(sender_number, sender_name)
                        mold_removal_data[sender_number].pop(
                            "awaiting_mold_confirmation", None
                        )
                    elif button_id == "mold_confirm_no":
                        send_text_message(
                            sender_number,
                            "Let's update your mold details. Please select 'Request a Quotation' to restart.",
                        )
                        mold_removal_data.pop(sender_number, None)
                        mold.send_mold_option_prompt(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif button_id == "add_area_yes":
                        mold.process_add_area_confirmation(
                            sender_number,
                            "yes",
                            mold_removal_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif button_id == "add_area_no":
                        mold.process_add_area_confirmation(
                            sender_number,
                            "no",
                            mold_removal_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif button_id == "onsite_inspect_yes":
                        mold_removal_data[sender_number]["onsite_inspection"] = True
                        send_text_message(
                            sender_number,
                            "Thank you! We will arrange an onsite inspection. A live agent will follow up shortly.",
                        )
                        initiate_live_agent(sender_number, sender_name)
                    elif button_id == "onsite_inspect_no":
                        mold_removal_data[sender_number]["onsite_inspection"] = False
                        send_text_message(
                            sender_number,
                            "Understood! We can proceed with a remote assessment. A live agent will assist you shortly.",
                        )
                        initiate_live_agent(sender_number, sender_name)

                elif "list_reply" in interactive_data:
                    list_id = interactive_data["list_reply"]["id"]

                    # Car Fumigation Flow
                    if list_id == "car_fumigation":
                        car_fumigation.send_car_fumigation_options(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif list_id in [
                        "car_fumigation_cockroach",
                        "car_fumigation_ants",
                        "car_fumigation_lizards",
                        "car_fumigation_multiple",
                        "car_fumigation_others",
                    ]:
                        car_fumigation.process_car_fumigation_pest(
                            sender_number,
                            list_id,
                            car_fumigation_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                        )
                    elif list_id.startswith("vehicle_"):
                        car_fumigation.process_vehicle_model_selection(
                            sender_number,
                            list_id,
                            car_fumigation_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                        )
                    elif list_id.startswith("location_"):
                        car_fumigation_data.setdefault(sender_number, {})[
                            "location"
                        ] = list_id
                        car_fumigation.compute_and_send_quote(
                            sender_number,
                            car_fumigation_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif list_id.startswith("cfq_"):
                        car_fumigation.process_car_fumigation_faq_response(
                            sender_number, list_id, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )

                    # Bedbug Flow
                    elif list_id == "bed_bugs":
                        bedbug.send_bedbug_initial_menu(
                            sender_number, PHONE_NUMBER_ID, ACCESS_TOKEN
                        )
                    elif list_id.startswith("bedbug_area_"):
                        bedbug.process_bedbug_area_selection(
                            sender_number,
                            list_id,
                            bedbug_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif list_id.startswith("bedbug_bed_count_"):
                        bedbug.process_bedbug_bedroom_count_selection(
                            sender_number,
                            list_id,
                            bedbug_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif list_id.startswith("bedbug_count_"):
                        bedbug.process_bedbug_count_selection(
                            sender_number,
                            list_id,
                            bedbug_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )

                    elif list_id.startswith("bbfaq_"):
                        bedbug.process_bedbug_faq_response(
                            sender_number,
                            list_id,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )

                    # NEW: Admin 'Bed Bug Confirm' from list
                    if (
                        sender_number in ADMIN_NUMBERS
                        and list_id == "admin_bedbug_confirm"
                    ):
                        target = ADMIN_TARGET.get(sender_number, sender_number)
                        bedbug.process_bedbug_faq_response(
                            target,
                            "bbfaq_preparation",
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                        send_text_message(
                            sender_number, "Admin command executed.")
                        return "OK", 200

                    # Mold Flow
                    elif list_id.startswith("area_"):
                        mold.process_mold_area_selection(
                            sender_number,
                            list_id,
                            mold_removal_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif list_id in ["growth_ceiling", "growth_walls", "growth_both"]:
                        mold.process_growth_location_choice(
                            sender_number,
                            list_id,
                            mold_removal_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            send_text_message,
                        )
                    elif list_id.startswith("mfaq_"):
                        mold.process_mold_faq_response(
                            sender_number,
                            list_id,
                            mold_removal_data,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                        )
                    elif list_id.startswith("bedroom_count_"):
                        if list_id == "bedroom_count_1":
                            mold_removal_data[sender_number][
                                "bedroom_count"
                            ] = "1 bedroom"
                        elif list_id == "bedroom_count_2":
                            mold_removal_data[sender_number][
                                "bedroom_count"
                            ] = "2 bedrooms"
                        else:
                            mold_removal_data[sender_number][
                                "bedroom_count"
                            ] = "3+ bedrooms"
                        mold_removal_data[sender_number].pop(
                            "awaiting_bedroom_count", None
                        )
                        mold.send_add_area_confirmation_prompt(
                            sender_number,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            mold_removal_data,
                        )
                    elif list_id.startswith("bathroom_count_"):
                        if list_id == "bathroom_count_1":
                            mold_removal_data[sender_number][
                                "bathroom_count"
                            ] = "1 bathroom"
                        elif list_id == "bathroom_count_2":
                            mold_removal_data[sender_number][
                                "bathroom_count"
                            ] = "2 bathrooms"
                        else:
                            mold_removal_data[sender_number][
                                "bathroom_count"
                            ] = "3+ bathrooms"
                        mold_removal_data[sender_number].pop(
                            "awaiting_bathroom_count", None
                        )
                        mold.send_add_area_confirmation_prompt(
                            sender_number,
                            PHONE_NUMBER_ID,
                            ACCESS_TOKEN,
                            mold_removal_data,
                        )
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
