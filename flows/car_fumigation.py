import os
import requests
import json
from dispatcher import get_user_state, set_user_state, clear_user_state, send_template_message, send_interactive_message

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE")

# =========================
# Helper: Send plain text
# =========================
def send_text_message(to: str, body: str):
    """
    Sends a simple text message to `to`. This is not a template,
    so it’s a session-message (legal if within 24h).
    """
    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        print(f"[send_text_message] Error {resp.status_code}: {resp.text}")
    return resp.json()

# ============================
# 1) Main Menu (Template)
# ============================
def send_main_menu(to: str, phone_number_id: str):
    """
    Sends the top-level main menu template (e.g. main_menu or main_menu_v2).
    This template has quick-reply buttons:
      - Need help on Pest! (id = "pest_control")
      - Need help on Mold! (id = "mold_removal")
      - Live Human (id = "live_human")
    """
    # If you want to personalize with the user’s name, switch to main_menu_v2 and pass [name].
    # For now, we’ll use `main_menu` which requires no parameters:
    send_template_message(to, template_name="main_menu", template_params=[])


# ===========================================================
# 2) Pest Control Services → Interactive List (Session Message)
# ===========================================================
def send_pest_control_list(to: str, phone_number_id: str):
    """
    Sends an interactive 'list' of pest control services.
    The row IDs must exactly match what dispatcher expects (e.g. "car_fumigation", "bedbugs", etc.).
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
                            {
                                "id": "car_fumigation",
                                "title": "Car Fumigation 🚗",
                                "description": "On-site fumigation & fogging"
                            },
                            {
                                "id": "bedbugs",
                                "title": "Bed Bugs 🛏️",
                                "description": "Elimination of bed bugs"
                            },
                            {
                                "id": "booklice",
                                "title": "Booklice 📚",
                                "description": "Treatment for booklice"
                            },
                            {
                                "id": "roaches_ants",
                                "title": "Roaches & Ants 🐜",
                                "description": "General pest control"
                            },
                            {
                                "id": "bees_wasps",
                                "title": "Bees/Wasps 🐝",
                                "description": "Removal of nests"
                            },
                            {
                                "id": "commercial_pest",
                                "title": "Commercial Pest 🏢",
                                "description": "Services for offices"
                            },
                            {
                                "id": "other_pest_issues",
                                "title": "Other Pest Issues 🕷️",
                                "description": "Other pest problems"
                            }
                        ]
                    }
                ]
            }
        }
    }
    send_interactive_message(payload)

# ====================================================
# 3) Car Fumigation Menu → Template `car_fum_menu`
# ====================================================
def send_car_fum_menu(to: str, phone_number_id: str):
    """
    Sends the `car_fum_menu` template. It has quick replies:
      1) Request a Quotation           (id = "car_fum_quote")
      2) More Info on Service         (id = "car_fum_info")
      3) Return to Main Menu          (id = "return_main_menu")
    """
    send_template_message(to, template_name="car_fum_menu", template_params=[])

# ===========================================================
# 4) Car Fumigation Quote Options → Template `car_fum_quote_options`
# ===========================================================
def send_car_fum_quote_options(to: str, phone_number_id: str):
    """
    Sends the `car_fum_quote_options` template. It has quick replies:
      1) Book Now            (id = "car_fum_book")
      2) More Info on Service (id = "car_fum_info")
      3) Return to Main Menu  (id = "return_main_menu")
    """
    send_template_message(to, template_name="car_fum_quote_options", template_params=[])

# =========================================================
# 5) Car Fumigation Appointment Method → `car_fum_appointment_method`
# =========================================================
def send_car_fum_appointment_method(to: str, phone_number_id: str):
    """
    Sends the `car_fum_appointment_method` template. Buttons:
      1) ASAP           (id = "car_fum_asap")
      2) Enter Date/Time (id = "car_fum_schedule")
    """
    send_template_message(to, template_name="car_fum_appointment_method", template_params=[])

# =============================================================================
# 6) Car Fumigation Quote Summary → `car_fum_appointment_confirmation` template
# =============================================================================
def send_car_fum_quote_summary(to: str, phone_number_id: str,
                               estimated_total: str,
                               pest_reported: str,
                               preferred_dt: str,
                               parking_address: str,
                               vehicle_desc: str):
    """
    Sends a template with 5 body params:
      1) estimated_total
      2) pest_reported
      3) preferred_dt  (placeholder until user picks date/time/address)
      4) parking_address (placeholder until user picks)
      5) vehicle_desc
    Then the template shows quick‐reply buttons:
      - Yes  → id="car_fum_confirm_yes"
      - No   → id="car_fum_confirm_no"
    """
    params = [
        {"type": "text", "text": estimated_total},
        {"type": "text", "text": pest_reported},
        {"type": "text", "text": preferred_dt},
        {"type": "text", "text": parking_address},
        {"type": "text", "text": vehicle_desc}
    ]

    send_template_message(to, template_name="car_fum_appointment_confirmation", template_params=[p["text"] for p in params])

# ================================================================
# 7) Interactive List: Pest Type in Vehicle (Session Message)
# ================================================================
def send_pest_type_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of pest types inside vehicle:
      - cockroach        (id="cockroach")
      - ants             (id="ants")
      - lizards          (id="lizards")
      - other_pest       (id="other_pest")
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
                            {"id": "cockroach", "title": "Cockroaches 🪳", "description": ""},
                            {"id": "ants", "title": "Ants 🐜", "description": ""},
                            {"id": "lizards", "title": "Lizards 🦎", "description": ""},
                            {"id": "other_pest", "title": "Other Pest 🕷️", "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    send_interactive_message(payload)

# ============================================================
# 8) Interactive List: Vehicle Type (Session Message)
# ============================================================
def send_vehicle_type_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of vehicle types:
      - sedan           (id="sedan")
      - suv             (id="suv")
      - mpv             (id="mpv")
      - ultra_luxury    (id="ultra_luxury")
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
                            {"id": "sedan", "title": "Sedan 🚗", "description": ""},
                            {"id": "suv", "title": "SUV 🚙", "description": ""},
                            {"id": "mpv", "title": "MPV 🚐", "description": ""},
                            {"id": "ultra_luxury", "title": "Ultra Luxury 🚘", "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    send_interactive_message(payload)

# ===========================================================
# 9) Interactive List: Service Location (Session Message)
# ===========================================================
def send_location_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of service zones:
      - north_zone   (id="north_zone")
      - south_zone   (id="south_zone")
      - east_zone    (id="east_zone")
      - west_zone    (id="west_zone")
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
                            {"id": "east_zone", "title": "East Zone 🌅", "description": ""},
                            {"id": "west_zone", "title": "West Zone 🌃", "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    send_interactive_message(payload)

# ============================================================
# 10) Quote Calculation (Simple placeholder logic)
# ============================================================
def calculate_quote(state: dict) -> float:
    """
    A placeholder quote calculator. In real life, you'd
    use pest_type, vehicle_type, location, etc. For this demo,
    we return a fixed base plus a small surcharge.
    """
    base = 50.0
    pest_type = state.get("pest_type", "")
    vehicle_type = state.get("vehicle_type", "")
    location = state.get("location", "")

    # Simple surcharges:
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
