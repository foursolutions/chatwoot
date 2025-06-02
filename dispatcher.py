import os
import json
import requests
import redis
from flows import car_fumigation  # our new Car Fumigation flow
# The following imports exist as placeholders.
# You can wire them up later when you convert bedbug.py and mold.py.
import flows.bedbug as bedbug_flow
import flows.mold as mold_flow

# ====================
# Environment / Config
# ====================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE")

REDIS_URL = os.getenv("REDIS_URL")
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

# Prefix for Car Fumigation user-state in Redis
CARFUM_PREFIX = "carfum"

# Utility: Fetch/Save/Clear user state in Redis (JSON‐encoded dict)
def get_user_state(prefix: str, user_id: str) -> dict:
    key = f"{prefix}:{user_id}"
    raw = r.get(key)
    return json.loads(raw) if raw else {}

def set_user_state(prefix: str, user_id: str, state: dict):
    key = f"{prefix}:{user_id}"
    r.set(key, json.dumps(state), ex=3600)

def clear_user_state(prefix: str, user_id: str):
    key = f"{prefix}:{user_id}"
    r.delete(key)

# ===========================
# 360dialog/Meta HTTP Helpers
# ===========================
def send_template_message(to_phone: str, template_name: str, template_params=None):
    """
    Sends a template message (approved in 360dialog) to 'to_phone'.
    - template_name: the exact template name (case-sensitive) in your 360dialog dashboard
    - template_params: a list of strings that fill {{1}}, {{2}}, … in the template body.
    """
    if template_params is None:
        template_params = []

    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }

    body = {
        "to": to_phone,
        "type": "template",
        "template": {
            "namespace": TEMPLATE_NAMESPACE,
            "name": template_name,
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": param}
                        for param in template_params
                    ]
                }
            ]
        }
    }

    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code not in (200, 201):
        print(f"[send_template_message] Error {resp.status_code}: {resp.text}")
    return resp.json()

def send_interactive_message(payload: dict):
    """
    Sends a session-based interactive message (list or reply-button) to 360dialog.
    The payload dict must contain at least:
      {
        "to": "<PHONE_NUMBER>",
        "type": "interactive",
        "interactive": { ... }
      }
    """
    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        print(f"[send_interactive_message] Error {resp.status_code}: {resp.text}")
    return resp.json()

# ==========================
# Main Webhook Event Handler
# ==========================
def handle_event(payload: dict):
    """
    Called from main.py whenever a message/event arrives from Meta.
    We parse out contacts → message type → interactive or text, then route.
    """

    # 1. Sanity check: ensure this is a 'messages' event
    if payload.get("object") != "whatsapp_business_account":
        return

    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            val = change.get("value", {})
            messages = val.get("messages", [])
            metadata = val.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", PHONE_NUMBER_ID)

            for message in messages:
                from_number = message.get("from")  # e.g. "6591234567"
                msg_type = message.get("type")

                button_id = None
                list_id = None
                text_body = None

                # 2. Extract interactive/button or list replies
                if msg_type == "interactive":
                    interactive = message.get("interactive", {})
                    itype = interactive.get("type")
                    if itype == "button_reply":
                        button_id = interactive["button_reply"]["id"]
                    elif itype == "list_reply":
                        list_id = interactive["list_reply"]["id"]

                # 3. If not interactive, check if it's plain text
                elif msg_type == "text":
                    text_body = message["text"]["body"].strip().lower()

                # 4. Route based on button_id, list_id, or text
                route_user(from_number, button_id, list_id, text_body, phone_number_id)


def route_user(from_number, button_id, list_id, text_body, phone_number_id):
    """
    Using button_id, list_id, or text_body, decide what to do.
    We're focusing on the Car Fumigation flow first. Later,
    you can plug in bedbug_flow or mold_flow as needed.
    """

    # 1) If the user tapped a quick‐reply button on the main menu:
    #    e.g. “Need help on Pest!” has button_id = "pest_control"
    if button_id == "pest_control":
        # Send the Pest Control Services interactive list
        car_fumigation.send_pest_control_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        # Initialize state
        state = {"step": "sent_pest_list"}
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # 2) If user chose “Car Fumigation” from the Pest list:
    if list_id == "car_fumigation":
        # Send the Car Fumigation menu (template: car_fum_menu)
        car_fumigation.send_car_fum_menu(
            to=from_number,
            phone_number_id=phone_number_id
        )
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["step"] = "sent_car_fum_menu"
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # === Car Fumigation submenu buttons ===

    # 3) From Car Fumigation menu, user taps “Request a Quotation”:
    if button_id == "car_fum_quote":
        # Send list of Pest Types in Vehicle (cockroach, ants, lizards, other)
        car_fumigation.send_pest_type_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["step"] = "awaiting_pest_type"
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # 4) From Car Fumigation menu, user taps “More Info on Service”:
    if button_id == "car_fum_info":
        # Send plain‐text or a template with “More Info…” (you can customize this)
        text = (
            "Our on‐site Car Fumigation service uses a fogger machine, is "
            "non‐oily, odor‐free, and includes interior sanitization.\n"
            "Please tap 'Request a Quotation' if you'd like a quote."
        )
        car_fumigation.send_text_message(to=from_number, body=text)
        return

    # 5) From Car Fumigation menu, user taps “Return to Main Menu”:
    if button_id == "return_main_menu":
        # We’ll send the main_menu_v2 template (which has placeholders for name)
        # For now, we just send main_menu (no placeholders)
        car_fumigation.send_main_menu(to=from_number, phone_number_id=phone_number_id)
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    # 6) Car Fumigation: User selecting a Pest Type in a list:
    if list_id in ["cockroach", "ants", "lizards", "other_pest"]:
        pest_selected = list_id  # e.g. "cockroach"
        # Save pest_type and ask for vehicle type:
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["step"] = "awaiting_vehicle_type"
        state["pest_type"] = pest_selected
        set_user_state(CARFUM_PREFIX, from_number, state)

        # Send interactive list of Vehicle Types:
        car_fumigation.send_vehicle_type_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        return

    # 7) Car Fumigation: User selecting a Vehicle Type:
    if list_id in ["sedan", "suv", "mpv", "ultra_luxury"]:
        vehicle_selected = list_id  # e.g. "suv" or "ultra_luxury"
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["vehicle_type"] = vehicle_selected

        # If user selected “ultra_luxury”, we need a free‐text brand:
        if vehicle_selected == "ultra_luxury":
            state["step"] = "awaiting_luxury_brand"
            set_user_state(CARFUM_PREFIX, from_number, state)
            # Ask user to type the brand
            car_fumigation.send_text_message(
                to=from_number,
                body="Please type your luxury vehicle brand (e.g., Mercedes S-Class):"
            )
            return
        else:
            # Non‐luxury: move to location step
            state["step"] = "awaiting_location"
            set_user_state(CARFUM_PREFIX, from_number, state)
            # Send location list (zones)
            car_fumigation.send_location_list(
                to=from_number,
                phone_number_id=phone_number_id
            )
            return

    # 8) Car Fumigation: If we were awaiting a luxury brand (free‐text):
    state = get_user_state(CARFUM_PREFIX, from_number)
    if state.get("step") == "awaiting_luxury_brand" and text_body:
        luxury_brand = message_text = text_body  # raw text (brand)
        state["luxury_brand"] = luxury_brand
        state["step"] = "awaiting_location"
        set_user_state(CARFUM_PREFIX, from_number, state)

        # Now send location list
        car_fumigation.send_location_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        return

    # 9) Car Fumigation: User selecting a Location (list_id in ["north", "south", "east", "west"]):
    if list_id in ["north_zone", "south_zone", "east_zone", "west_zone"]:
        location_selected = list_id
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["location"] = location_selected
        # We can compute a quote here (for demo, we'll use a simple rate)
        quote_amount = car_fumigation.calculate_quote(state)
        state["quote"] = quote_amount
        state["step"] = "sent_quote_summary"
        set_user_state(CARFUM_PREFIX, from_number, state)

        # Send a template summarizing the quote with 5 parameters:
        # 1) Estimated Total, 2) pest_type, 3) Date/Time placeholder, 4) Parking Address placeholder, 5) Vehicle (or brand)
        car_fumigation.send_car_fum_quote_summary(
            to=from_number,
            phone_number_id=phone_number_id,
            estimated_total=f"${quote_amount:.2f}",
            pest_reported=state["pest_type"],
            preferred_dt="(Select Date/Time next)",   # placeholder text
            parking_address="(Select Address next)",
            vehicle_desc=(
                state["luxury_brand"]
                if state.get("vehicle_type") == "ultra_luxury"
                else state.get("vehicle_type", "")
            )
        )
        return

    # 10) User choosing an appointment‐method from `car_fum_appointment_method`:
    if button_id == "car_fum_asap":
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["appointment_method"] = "ASAP"
        state["step"] = "awaiting_parking_address"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_text_message(
            to=from_number,
            body="Got it. Please provide your parking address now."
        )
        return

    if button_id == "car_fum_schedule":
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["appointment_method"] = "Scheduled"
        state["step"] = "awaiting_date_time"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_text_message(
            to=from_number,
            body="Okay, please type your preferred date/time (e.g., 2025-06-10 14:00)."
        )
        return

    # 11) User typing date/time:
    state = get_user_state(CARFUM_PREFIX, from_number)
    if state.get("step") == "awaiting_date_time" and text_body:
        # For simplicity we accept any text as date/time (in production, validate format)
        state["preferred_date_time"] = text_body
        state["step"] = "awaiting_parking_address"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_text_message(
            to=from_number,
            body="Thanks. Now please provide your parking address."
        )
        return

    # 12) User typing parking address:
    if state.get("step") == "awaiting_parking_address" and text_body:
        state["parking_address"] = text_body
        state["step"] = "awaiting_vehicle_number"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_text_message(
            to=from_number,
            body="Got the parking address. Please type your vehicle number (e.g., SGA1234A)."
        )
        return

    # 13) User typing vehicle number:
    if state.get("step") == "awaiting_vehicle_number" and text_body:
        state["vehicle_number"] = text_body
        state["step"] = "awaiting_confirmation"
        set_user_state(CARFUM_PREFIX, from_number, state)

        # We already have a quote in state["quote"], pest/type, location, etc.
        car_fumigation.send_car_fum_appointment_confirmation(
            to=from_number,
            phone_number_id=phone_number_id,
            estimated_total=f"${state['quote']:.2f}",
            pest_reported=state["pest_type"],
            preferred_dt=state.get("preferred_date_time", "ASAP"),
            parking_address=state["parking_address"],
            vehicle_number=state["vehicle_number"]
        )
        return

    # 14) User responds "Yes" or "No" to appointment confirmation:
    if button_id == "car_fum_confirm_yes":
        # Finalize booking → escalate to a live human or send contact info
        car_fumigation.send_text_message(
            to=from_number,
            body=(
                "Great! Your appointment is confirmed. "
                "A human agent will reach out shortly to finalize details."
            )
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    if button_id == "car_fum_confirm_no":
        # Cancel or offer to go back to quote details
        car_fumigation.send_text_message(
            to=from_number,
            body="No problem. You can type 'restart' to begin again or tap 'Car Fumigation' from the main menu."
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    # 15) If no other case matched, you can always echo or send a help message:
    car_fumigation.send_text_message(
        to=from_number,
        body=(
            "Sorry, I didn’t understand that. Please tap 'Need help on Pest!' "
            "or type 'menu' to see options again."
        )
    )
