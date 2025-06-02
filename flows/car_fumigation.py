import os
import requests
import json
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_interactive_message,
    send_text_message
)

# ============================
# 1) Main Menu (Template)
# ============================
def send_main_menu(to: str, phone_number_id: str):
    """
    Sends the top‐level main menu template (main_menu_v2).
    This template has one body placeholder {{1}}, so we must supply exactly one non‐empty string.
    """
    greeting_name = "there"  # Replace "there" with a real username if you prefer
    resp = send_template_message(
        to=to,
        template_name="main_menu_v2",     # Exactly match your template name in 360dialog
        template_params=[greeting_name]   # One non‐empty string for {{1}}
    )
    print(f"[DEBUG] send_main_menu → 360dialog response: {resp}")


# ===========================================================
# 2) Pest Control Services → Interactive List (Session Message)
# ===========================================================
def send_pest_control_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of pest control services.
    Each row’s `id` must match what dispatcher checks (e.g. "car_fumigation").
    """
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Pest Control Services"},
            "body": {"text": "Please select the pest control service you need assistance with:"},
            "footer": {"text": "Tap below to choose"},
            "action": {
                "button": "Select Service",
                "sections": [
                    {
                        "title": "Common Pest Issues",
                        "rows": [
                            {"id": "car_fumigation",    "title": "Car Fumigation 🚗",    "description": "On‐site fumigation & fogging"},
                            {"id": "bedbugs",            "title": "Bed Bugs 🛏️",         "description": "Elimination of bed bugs"},
                            {"id": "booklice",           "title": "Booklice 📚",         "description": "Treatment for booklice"},
                            {"id": "roaches_ants",       "title": "Roaches & Ants 🐜",   "description": "General pest control"},
                            {"id": "bees_wasps",         "title": "Bees/Wasps 🐝",       "description": "Removal of nests"},
                            {"id": "commercial_pest",    "title": "Commercial Pest 🏢",  "description": "Services for offices"},
                            {"id": "other_pest_issues",  "title": "Other Pest Issues 🕷️", "description": "Other pest problems"}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_pest_control_list → 360dialog response: {resp}")


# ===========================================================
# 3) Car Fumigation Menu → Template `car_fum_menu`
# ===========================================================
def send_car_fum_menu(to: str, phone_number_id: str):
    """
    Sends the `car_fum_menu` template with quick‐reply button IDs:
      - "car_fum_quote"
      - "car_fum_info"
      - "return_main_menu"
    """
    resp = send_template_message(
        to=to,
        template_name="car_fum_menu",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_menu → 360dialog response: {resp}")


# ===========================================================
# 4) Car Fumigation Quote Options → Template `car_fum_quote_options`
# ===========================================================
def send_car_fum_quote_options(to: str, phone_number_id: str):
    """
    Sends the `car_fum_quote_options` template with quick‐reply button IDs:
      - "car_fum_book"
      - "car_fum_info"
      - "return_main_menu"
    """
    resp = send_template_message(
        to=to,
        template_name="car_fum_quote_options",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_quote_options → 360dialog response: {resp}")


# ==========================================================
# 5) Car Fumigation Appointment Method → `car_fum_appointment_method`
# ==========================================================
def send_car_fum_appointment_method(to: str, phone_number_id: str):
    """
    Sends the `car_fum_appointment_method` template with buttons:
      - "car_fum_asap"
      - "car_fum_schedule"
    """
    resp = send_template_message(
        to=to,
        template_name="car_fum_appointment_method",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_appointment_method → 360dialog response: {resp}")


# =============================================================================
# 6) Car Fumigation Quote Summary → Template `car_fum_appointment_confirmation`
# =============================================================================
def send_car_fum_quote_summary(to: str, phone_number_id: str,
                               estimated_total: str,
                               pest_reported: str,
                               preferred_dt: str,
                               parking_address: str,
                               vehicle_desc: str):
    """
    Sends a template (car_fum_appointment_confirmation) with 5 body params:
      1) estimated_total
      2) pest_reported
      3) preferred_dt
      4) parking_address
      5) vehicle_desc

    The template shows two quick‐reply buttons:
      - "car_fum_confirm_yes"
      - "car_fum_confirm_no"
    """
    params = [
        {"type": "text", "text": estimated_total},
        {"type": "text", "text": pest_reported},
        {"type": "text", "text": preferred_dt},
        {"type": "text", "text": parking_address},
        {"type": "text", "text": vehicle_desc}
    ]
    resp = send_template_message(
        to=to,
        template_name="car_fum_appointment_confirmation",
        template_params=[p["text"] for p in params]
    )
    print(f"[DEBUG] send_car_fum_quote_summary → 360dialog response: {resp}")


# =============================================================================
# 7) Final “Appointment Confirmation” Alias
# =============================================================================
def send_car_fum_appointment_confirmation(to: str, phone_number_id: str,
                                          estimated_total: str,
                                          pest_reported: str,
                                          preferred_dt: str,
                                          parking_address: str,
                                          vehicle_number: str):
    """
    Alias for send_car_fum_quote_summary. Used by dispatcher in Step 13.
    """
    # Reuse the same template (car_fum_appointment_confirmation)
    send_car_fum_quote_summary(
        to=to,
        phone_number_id=phone_number_id,
        estimated_total=estimated_total,
        pest_reported=pest_reported,
        preferred_dt=preferred_dt,
        parking_address=parking_address,
        vehicle_desc=vehicle_number
    )


# ================================================================
# 8) Interactive List: Pest Type in Vehicle (Session Message)
# ================================================================
def send_pest_type_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of pest types inside the vehicle:
      - cockroach  (id="cockroach")
      - ants       (id="ants")
      - lizards    (id="lizards")
      - other_pest (id="other_pest")
    """
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Select Pest Type"},
            "body": {"text": "Which pest are you seeing inside your vehicle?"},
            "footer": {"text": "Tap to choose"},
            "action": {
                "button": "Select Pest Type",
                "sections": [
                    {
                        "title": "Vehicle Pest Types",
                        "rows": [
                            {"id": "cockroach",  "title": "Cockroaches 🪳", "description": ""},
                            {"id": "ants",       "title": "Ants 🐜",        "description": ""},
                            {"id": "lizards",    "title": "Lizards 🦎",    "description": ""},
                            {"id": "other_pest", "title": "Other Pest 🕷️", "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_pest_type_list → 360dialog response: {resp}")


# ============================================================
# 9) Interactive List: Vehicle Type (Session Message)
# ============================================================
def send_vehicle_type_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of vehicle types:
      - sedan         (id="sedan")
      - suv           (id="suv")
      - mpv           (id="mpv")
      - ultra_luxury  (id="ultra_luxury")
    """
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Select Vehicle Type"},
            "body": {"text": "What type of vehicle do you drive?"},
            "footer": {"text": "Tap to choose"},
            "action": {
                "button": "Select Vehicle Type",
                "sections": [
                    {
                        "title": "Vehicle Types",
                        "rows": [
                            {"id": "sedan",         "title": "Sedan 🚗",         "description": ""},
                            {"id": "suv",           "title": "SUV 🚙",           "description": ""},
                            {"id": "mpv",           "title": "MPV 🚐",           "description": ""},
                            {"id": "ultra_luxury",  "title": "Ultra Luxury 🚘",  "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_vehicle_type_list → 360dialog response: {resp}")


# ===========================================================
# 10) Interactive List: Service Location (Session Message)
# ===========================================================
def send_location_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of service zones:
      - north_zone  (id="north_zone")
      - south_zone  (id="south_zone")
      - east_zone   (id="east_zone")
      - west_zone   (id="west_zone")
    """
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Select Service Zone"},
            "body": {"text": "Which zone is your vehicle located in?"},
            "footer": {"text": "Tap to choose"},
            "action": {
                "button": "Select Zone",
                "sections": [
                    {
                        "title": "Service Zones",
                        "rows": [
                            {"id": "north_zone", "title": "North Zone 🌆", "description": ""},
                            {"id": "south_zone", "title": "South Zone 🌇", "description": ""},
                            {"id": "east_zone",  "title": "East Zone 🌅",  "description": ""},
                            {"id": "west_zone",  "title": "West Zone 🌃",  "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_location_list → 360dialog response: {resp}")


# ============================================================
# 11) Quote Calculation (Placeholder Logic)
# ============================================================
def calculate_quote(state: dict) -> float:
    """
    A placeholder quote calculator. In production, replace with real logic.
    Example: base + surcharges based on pest, vehicle type, zone.
    """
    base = 50.0
    pest_type = state.get("pest_type", "")
    vehicle_type = state.get("vehicle_type", "")
    location = state.get("location", "")

    surcharges = 0.0
    if pest_type == "cockroach":
        surcharges += 10
    elif pest_type == "ants":
        surcharges += 5
    if vehicle_type == "ultra_luxury":
        surcharges += 25
    if location in ["north_zone", "south_zone", "east_zone", "west_zone"]:
        surcharges += 10

    return base + surcharges


# ──────────────────────────────────────────────────────────────────────────────
#  X) Universal flow‐handler stub. Dispatcher will call this on every
#     interactive (list) or button payload.
# ──────────────────────────────────────────────────────────────────────────────
def handle_car_fumigation_flow(from_number: str, message: dict, user_state: dict):
    """
    1) Decide whether this is a quick‐reply button or an interactive list reply.
    2) Read the payload or button text.
    3) Update Redis state accordingly.
    4) Call the next send_*() function to continue the flow.
    """

    prefix = "carfum"
    msg_type = message.get("type")

    # ─── 1) Handle quick‐reply buttons ───
    if msg_type == "button":
        payload = message["button"]["payload"]  # e.g., "Need help on Pest!" or "car_fum_quote"
        print(f"[DEBUG] handle_car_fumigation_flow: BUTTON payload='{payload}' from {from_number}")

        # ---- A) If user tapped “Need help on Pest!” on main_menu_v2 ----
        if payload.lower() == "need help on pest!":
            # Clear any old state
            clear_user_state(prefix, from_number)

            # Set new state to indicate we’re in the “choose pest service” step
            new_state = {"step": "choose_service"}
            set_user_state(prefix, from_number, new_state)

            # Send the interactive list of pest control services
            send_pest_control_list(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # ---- B) If user tapped “Get Quote” on car_fum_menu ----
        elif payload.lower() in ["get quote", "car_fum_quote"]:
            state = user_state or {}
            state["step"] = "select_quote_option"
            set_user_state(prefix, from_number, state)

            send_car_fum_quote_options(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # ---- C) If user tapped “car_fum_info” on car_fum_menu ----
        elif payload.lower() == "car_fum_info":
            send_text_message(
                to=from_number,
                body=(
                    "Our car fumigation service uses non‐oily fogging. "
                    "Prices start at SGD 50 for a basic treatment. "
                    "Type 'reset' to go back anytime."
                )
            )
            return

        # ---- D) If user tapped “Return Main Menu” ----
        elif payload.lower() == "return_main_menu":
            clear_user_state(prefix, from_number)
            send_main_menu(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        else:
            print(f"[DEBUG] Unhandled BUTTON payload: '{payload}'")
            send_text_message(
                to=from_number,
                body="Sorry, I didn’t understand that button. Type 'reset' to start over."
            )
            return

    # ─── 2) Handle interactive list replies ───
    elif msg_type == "interactive":
        interactive_payload = message["interactive"]
        print(f"[DEBUG] handle_car_fumigation_flow: INTERACTIVE payload='{json.dumps(interactive_payload)}' from {from_number}")

        state = user_state or {}
        step = state.get("step")

        # ---- A) If we’re in “choose_service”, user saw the Pest Control Services list ----
        if step == "choose_service":
            selected_id = interactive_payload["list_reply"]["id"]  # e.g., "car_fumigation"
            print(f"[DEBUG] Selected pest service: '{selected_id}'")

            if selected_id == "car_fumigation":
                state["step"] = "car_fum_menu"
                set_user_state(prefix, from_number, state)

                send_car_fum_menu(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            elif selected_id == "bedbugs":
                send_text_message(
                    to=from_number,
                    body="Bed Bugs service is coming soon! Type 'reset' to go back."
                )
                return

            else:
                send_text_message(
                    to=from_number,
                    body="Sorry, that service is not available yet. Type 'reset' to start over."
                )
                return

        # ---- B) If we’re in “select_quote_option”, user saw car_fum_quote_options list (if implemented) ----
        # elif step == "select_quote_option":
        #     (…additional logic here…)
        #     return

        else:
            print(f"[DEBUG] Interactive received, but unknown step='{step}' for {from_number}")
            send_text_message(
                to=from_number,
                body="Sorry, I didn’t understand that. Type 'reset' to start over."
            )
            return

    # ─── 3) Fallback for any other payload types ───
    else:
        print(f"[DEBUG] handle_car_fumigation_flow: Unsupported msg_type='{msg_type}'")
        send_text_message(
            to=from_number,
            body="Sorry, I can’t handle that type of message. Type 'reset' to start over."
        )
        return
