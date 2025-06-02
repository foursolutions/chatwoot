# flows/car_fumigation.py

import os
import requests
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
    Sends the top‐level main menu template (main_menu).
    This template expects exactly 1 body parameter (e.g., a greeting).
    """
    # If your template expects something like "Welcome, {{1}}", replace "" with a real greeting.
    params = [""]
    resp = send_template_message(
        to=to,
        template_name="main_menu",
        template_params=params
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
    send_interactive_message(payload)


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
    send_template_message(to, template_name="car_fum_menu", template_params=[])


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
    send_template_message(to, template_name="car_fum_quote_options", template_params=[])


# ==========================================================
# 5) Car Fumigation Appointment Method → `car_fum_appointment_method`
# ==========================================================
def send_car_fum_appointment_method(to: str, phone_number_id: str):
    """
    Sends the `car_fum_appointment_method` template with buttons:
      - "car_fum_asap"
      - "car_fum_schedule"
    """
    send_template_message(to, template_name="car_fum_appointment_method", template_params=[])


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
    send_template_message(
        to,
        template_name="car_fum_appointment_confirmation",
        template_params=[p["text"] for p in params]
    )


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
    send_interactive_message(payload)


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
    send_interactive_message(payload)


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
    send_interactive_message(payload)


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
