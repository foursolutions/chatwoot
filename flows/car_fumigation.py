# flows/car_fumigation.py

import os
from datetime import datetime, timedelta

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_interactive_message,
    send_text_message
)

# ─── Internal alert numbers (without "+" or spaces) ───
ALERT_NUMBERS = [
    "6588662359",  # Bot number +65 88662359
    "6587788080",  # Company number +65 87788080
    "6580681688",  # Sales in charge +65 80681688
]

# =====================================================================
# 1) Main Menu (Template)
# =====================================================================
def send_main_menu(to: str, phone_number_id: str):
    greeting_name = "there"
    resp = send_template_message(
        to=to,
        template_name="main_menu_v2",
        template_params=[greeting_name]
    )
    print(f"[DEBUG] send_main_menu → 360dialog response: {resp}")


# =====================================================================
# 2) Pest Control Services → Interactive List
# =====================================================================
def send_pest_control_list(to: str, phone_number_id: str):
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
                            {"id": "car_fumigation",    "title": "Car Fumigation 🚗",    "description": "On-site fumigation & fogging"},
                            {"id": "bedbugs",           "title": "Bed Bugs 🛏️",         "description": "Elimination of bed bugs"},
                            {"id": "booklice",          "title": "Booklice 📚",         "description": "Treatment for booklice"},
                            {"id": "roaches_ants",      "title": "Roaches & Ants 🐜",   "description": "General pest control"},
                            {"id": "bees_wasps",        "title": "Bees/Wasps 🐝",       "description": "Removal of nests"},
                            {"id": "commercial_pest",   "title": "Commercial Pest 🏢",  "description": "Services for offices"},
                            {"id": "other_pest_issues", "title": "Other Pest Issues 🕷️", "description": "Other pest problems"}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_pest_control_list → 360dialog response: {resp}")


# =====================================================================
# 3) Car Fumigation Menu → Template `car_fum_menu`
# =====================================================================
def send_car_fum_menu(to: str, phone_number_id: str):
    resp = send_template_message(
        to=to,
        template_name="car_fum_menu",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_menu → 360dialog response: {resp}")


# =====================================================================
# 4) Car Fumigation Info / Quote Options → Template `car_fum_quote_options`
# =====================================================================
def send_car_fum_quote_options(to: str, phone_number_id: str):
    resp = send_template_message(
        to=to,
        template_name="car_fum_quote_options",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_quote_options → 360dialog response: {resp}")


# =====================================================================
# 5) “Select Pest Type” → Interactive List
# =====================================================================
def send_pest_type_list(to: str, phone_number_id: str):
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


# =====================================================================
# 6) “Select Vehicle Type” → Interactive List
# =====================================================================
def send_vehicle_type_list(to: str, phone_number_id: str):
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
                            {"id": "vehicle_sedan",        "title": "Sedan/Hatchback",            "description": "Standard cars"},
                            {"id": "vehicle_suv",          "title": "SUV",                         "description": "Sport Utility Vehicle"},
                            {"id": "vehicle_mpv",          "title": "MPV",                         "description": "Multi-Purpose Vehicle"},
                            {"id": "vehicle_vans",         "title": "Vans/Lorries",                "description": "Commercial vehicles"},
                            {"id": "vehicle_ultra_luxury", "title": "Super/Luxury Cars",           "description": "e.g. Bentley, Ferrari, Lamborghini, Rolls Royce equivalent"},
                            {"id": "vehicle_others",       "title": "Others",                      "description": "Other vehicle types"}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_vehicle_type_list → 360dialog response: {resp}")


# =====================================================================
# 7) “Additional Care Fee” → Quick-Reply Buttons (Luxury-Brand Prompt)
# =====================================================================
def send_cfadditionalfee_prompt(to: str, phone_number_id: str):
    text = (
        "Does your vehicle belong to any of these brands?\n\n"
        "Mercedes-Benz\n"
        "BMW\n"
        "Audi\n"
        "Lexus\n"
        "Porsche\n"
        "Jaguar\n"
        "Tesla\n"
        "Range Rover\n\n"
        "These brands require special care during servicing.\n"
        "Please reply Yes or No."
    )
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "luxury_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "luxury_no",  "title": "No"}}
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_cfadditionalfee_prompt → 360dialog response: {resp}")


# =====================================================================
# Utility: Send a dynamic list of the next 7 dates
# =====================================================================
def send_upcoming_dates_list(to: str, phone_number_id: str):
    today = datetime.now()
    # Start from day after tomorrow (today + 2 days)
    base = today + timedelta(days=2)
    rows = []
    for i in range(7):
        date_obj = base + timedelta(days=i)
        date_str = date_obj.strftime("%d-%m-%Y")
        weekday = date_obj.strftime("%A")
        title = f"{date_str}, {weekday}"
        rows.append({
            "id": f"date_{date_str}",
            "title": title,
            "description": ""
        })
    # Add "Other dates" at the end
    rows.append({
        "id": "other_dates",
        "title": "Other dates",
        "description": "Select a different date using DD-MM-YYYY"
    })

    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Choose a Date"},
            "body": {"text": "Please select one of the following dates:"},
            "footer": {"text": "Tap to choose"},
            "action": {
                "button": "Select Date",
                "sections": [
                    {
                        "title": "Available Dates",
                        "rows": rows
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_upcoming_dates_list → 360dialog response: {resp}")


# =====================================================================
# 8) “Select Location” → Interactive List
# =====================================================================
def send_location_selection(to: str, phone_number_id: str):
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "On-Site Location Selection"},
            "body": {"text": "Please select the location nearest to the address where your vehicle will be parked:"},
            "footer": {"text": "Tap below to choose"},
            "action": {
                "button": "Select Location",
                "sections": [
                    {
                        "title": "Locations",
                        "rows": [
                            {"id": "location_north",     "title": "North",                  "description": "Woodlands, Yishun, Sembawang, etc"},
                            {"id": "location_northeast", "title": "North-East",             "description": "Hougang, Sengkang, Punggol, etc."},
                            {"id": "location_central",   "title": "Central",                "description": "Orchard, Newton, River Valley, etc."},
                            {"id": "location_east",      "title": "East",                   "description": "Bedok, Changi, Tampines, etc."},
                            {"id": "location_west",      "title": "West",                   "description": "Jurong, Clementi, Bukit Batok, etc."},
                            {"id": "location_south",     "title": "South",                  "description": "Bukit Merah, Bukit Timah, Queenstown"},
                            {"id": "location_sentosa",   "title": "Sentosa & Restricted",   "description": "Sentosa, Tuas & restricted areas"}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_location_selection → 360dialog response: {resp}")


# =====================================================================
# 9) “Which Day?” → Interactive Button Prompt (Today, Tomorrow, Pick a Date)
# =====================================================================
def send_day_selection_prompt(to: str, phone_number_id: str):
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Which day would you like to book?\n\nTap one of the options below:"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "day_today",    "title": "Today"}},
                    {"type": "reply", "reply": {"id": "day_tomorrow", "title": "Tomorrow"}},
                    {"type": "reply", "reply": {"id": "day_pick",     "title": "Pick a Date"}}
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_day_selection_prompt → {resp}")


# =====================================================================
# 10) “Which Time?” → Interactive Button Prompt (max 3 buttons)
# =====================================================================
def send_time_selection_prompt(to: str, phone_number_id: str, chosen_date: str):
    state = get_user_state("carfum", to) or {}
    state["appointment_date"] = chosen_date
    set_user_state("carfum", to, state)

    # Determine weekday name for chosen_date
    try:
        weekday_name = datetime.strptime(chosen_date, "%d-%m-%Y").strftime("%A")
    except Exception:
        weekday_name = ""

    text = (
        f"You chose {chosen_date} ({weekday_name}) for your appointment.\n\n"
        "Please select your preferred time:\n"
        "• Morning (10AM to 12PM)\n"
        "• Afternoon (12PM to 6PM)\n"
        "• Evening (6PM to 11:59PM)\n\n"
        "If you need a different time, simply type it (e.g. \"18:30\" or \"6:30pm\")."
    )
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "time_morning",   "title": "Morning"}},
                    {"type": "reply", "reply": {"id": "time_afternoon", "title": "Afternoon"}},
                    {"type": "reply", "reply": {"id": "time_evening",   "title": "Evening"}}
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_time_selection_prompt → {resp}")


# =====================================================================
# 11) “Quote Summary” → Interactive Button Template
# =====================================================================
def send_quote_summary(to: str, phone_number_id: str):
    state = get_user_state("carfum", to) or {}

    if state.get("manual_quote", False):
        # User selected Super/Luxury Cars or Others → show "Require agent to quote"
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Below is the estimated breakdown of your quotation:\n\n"
            "- Car Model Type Pricing: Require agent to quote\n"
            "- Additional Care Fee: Require agent to quote\n"
            "- On-site Service Charge: Require agent to quote\n\n"
            "Estimated Total: Your vehicle or service request requires an agent quotation. "
            "Please allow our agent to assist you further.\n\n"
            "Please select an option below:"
        )
    else:
        # Compute base, fee, location charge
        vehicle = state.get("vehicle", "")
        if vehicle == "vehicle_sedan":
            base_quote = 140
        elif vehicle == "vehicle_suv":
            base_quote = 150
        elif vehicle == "vehicle_mpv":
            base_quote = 160
        elif vehicle == "vehicle_vans":
            base_quote = 170
        else:
            base_quote = 0

        additional_fee = 10 if state.get("continental") == "luxury_yes" else 0

        loc = state.get("location", "")
        if loc in ["location_north", "location_northeast", "location_east"]:
            location_charge = 20
        elif loc in ["location_central", "location_west", "location_south"]:
            location_charge = 25
        elif loc == "location_sentosa":
            location_charge = 40
        else:
            location_charge = 0

        computed_quote = base_quote + additional_fee + location_charge
        state["computed_quote"] = computed_quote
        set_user_state("carfum", to, state)

        additional_fee_str = f"${additional_fee}" if additional_fee != 0 else "$0"
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Below is the estimated breakdown of your quotation:\n\n"
            f"- Car Model Type Pricing: ${base_quote}\n"
            f"- Additional Care Fee: {additional_fee_str}\n"
            f"- On-site Service Charge: ${location_charge}\n\n"
            f"Estimated Total: ${computed_quote}\n\n"
            "Please select an option below:"
        )

    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "button",
            "body": {"text": summary_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "book_appointment", "title": "Book Now"}},
                    {"type": "reply", "reply": {"id": "fumigation_faq",   "title": "More Info on Service"}},
                    {"type": "reply", "reply": {"id": "return_main_menu", "title": "Return to Main Menu"}}
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_quote_summary → 360dialog response: {resp}")


# =====================================================================
# 12) Car Fumigation FAQ Interactive List
# =====================================================================
def send_car_fumigation_faq(to, phone_number_id: str):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Car Fumigation FAQ"},
            "body": {"text": "Select a FAQ question:"},
            "footer": {"text": "Tap an option"},
            "action": {
                "button": "Select FAQ",
                "sections": [{
                    "title": "FAQ Questions",
                    "rows": [
                        {"id": "cfq_safe",       "title": "Is it safe? Kids/Pets",   "description": "Safety with HACCP chemicals"},
                        {"id": "cfq_included",   "title": "Service Details",          "description": "What's included in our service?"},
                        {"id": "cfq_warranty",   "title": "Our Warranty",            "description": "Warranty information"},
                        {"id": "cfq_preparation","title": "Preparation",             "description": "What to prepare before service"},
                        {"id": "cfq_duration",   "title": "Service Duration",        "description": "How long the service takes"},
                        {"id": "cfq_payment",    "title": "Payment Options",         "description": "Payment methods accepted"}
                    ]
                }]
            }
        }
    }
    send_interactive_message(payload)


def process_car_fumigation_faq_response(to: str, faq_id: str):
    faq_answers = {
        "cfq_safe": (
            "Our car fumigation service ensures safety for your children and pets through:\n"
            "• NEA HACCP-certified chemicals, safe even for Food & Beverage environments.\n"
            "• Non-oily solutions, reducing chemical residues.\n"
            "• Completely odorless treatment.\n"
            "• Professional fogging equipment, avoiding aerosol residues from off-the-shelf products."
        ),
        "cfq_included": (
            "Our car fumigation service includes:\n"
            "• Odorless, non-oily, HACCP-grade chemical application.\n"
            "• Professional fogging machinery.\n"
            "• Complete interior disinfecting wipe-down.\n"
            "• Vacuuming to remove all dead pests.\n"
            "• Application of a residual protective coating lasting up to 3 months."
        ),
        "cfq_warranty": (
            "Warranty eligibility is assessed by our on-site technician post-service, provided no cockroaches are found after treatment.\n"
            "Warranty terms:\n"
            "• Effective from 1 week after initial servicing, lasting an additional 3 weeks (total 1-month coverage).\n"
            "• One-time complimentary car fumigation at the original service location.\n"
            "Please allow 7-14 working days for warranty appointment scheduling; earlier slots may be available."
        ),
        "cfq_preparation": (
            "Please follow these preparation steps:\n"
            "* Remove personal items including baby seats, perfume, sunglasses, tissues, pillows, soft toys, valuables, and food items.\n"
            "* Completely empty the car boot for effective treatment.\n"
            "* Park your car in a location that allows easy access for our technician.\n"
            "* Provide space for our technician to safely set up equipment and perform the service.\n"
            "* You will receive notifications before arrival and completion.\n"
            "* Inform us at least 2 hours before the appointment if you need to reschedule.\n"
            "A clutter-free car enhances the effectiveness of our service."
        ),
        "cfq_duration": (
            "Our car fumigation typically takes between 1.5 to 2 hours, though it may vary depending on the situation.\n"
            "You can continue with your daily activities as your presence is not required during the entire process."
        ),
        "cfq_payment": (
            "We accept the following payment methods:\n"
            "* PayNow: Payment via UEN: 201812722M\n"
            "* Atome: Interest-free installment payments (3 months) with a 5% surcharge.\n"
            "* Cash: Please inform us if you prefer cash and prepare the exact amount."
        )
    }
    answer = faq_answers.get(faq_id, "Sorry, no information is available for that question.")
    send_text_message(to, answer)


# =====================================================================
# 13) Universal flow-handler: handle_car_fumigation_flow
# =====================================================================
def handle_car_fumigation_flow(from_number: str, message: dict, user_state: dict):
    """
    1) Determine whether this is a quick-reply button (message["type"] == "button"),
       an interactive list reply (message["interactive"]["type"] == "list_reply"),
       or plain text (for "collect_*" steps).
    2) Extract payload/text, compare to current user_state["step"].
    3) Update Redis state accordingly.
    4) Call next send_*() function to continue the flow.
    """
    prefix = "carfum"
    msg_type = message.get("type")  # "text", "button", or "interactive"

    # ─── Helper to extract quick-reply payload ───
    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"]["payload"]
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"]["id"]
        return ""

    # Retrieve or initialize state
    state = user_state or {}
    step = state.get("step", "")

    # ----------------------------------------------------------------
    # 1) FAQ Handling: if step == "car_faq", handle FAQ replies first
    # ----------------------------------------------------------------
    # A) FAQ replies from button payloads
    if step == "car_faq" and msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload and payload.startswith("cfq_"):
            process_car_fumigation_faq_response(from_number, payload)
            # Re-show FAQ list
            send_car_fumigation_faq(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # B) FAQ replies from interactive list (list_reply)
    if step == "car_faq" and msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        if selected_id.startswith("cfq_"):
            process_car_fumigation_faq_response(from_number, selected_id)
            # Re-show FAQ list
            send_car_fumigation_faq(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # ----------------------------------------------------------------
    # 2) Handle quick-reply BUTTONS (either "button" or "interactive.button_reply")
    # ----------------------------------------------------------------
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_car_fumigation_flow: BUTTON/BR payload='{payload_lower}' from {from_number}")
            state = user_state or {}
            step = state.get("step", "")

            # A) “Need help on Pest!” from main menu
            if payload_lower == "need help on pest!":
                clear_user_state(prefix, from_number)
                new_state = {"step": "choose_service"}
                set_user_state(prefix, from_number, new_state)
                send_pest_control_list(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # B) “More Info on Service” at any point → go to FAQ
            if payload_lower in ["more info on service", "fumigation_faq"]:
                state["step"] = "car_faq"
                set_user_state(prefix, from_number, state)
                send_car_fumigation_faq(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # C) “Return to Main Menu”
            if payload_lower in ["return to main menu", "return_main_menu"]:
                clear_user_state(prefix, from_number)
                send_main_menu(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # D) “Book Now” on quote summary → Ask “Which Day?”
            if step == "show_quote_summary" and payload_lower in ["book_appointment", "yes", "car_fum_confirm_yes"]:
                state["step"] = "collect_day_option"
                set_user_state(prefix, from_number, state)
                send_day_selection_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # E) “No” on final quote summary → back to quote summary
            if step == "show_quote_summary" and payload_lower in ["no", "return_to_quote", "car_fum_confirm_no"]:
                state["step"] = "select_location"
                set_user_state(prefix, from_number, state)
                send_quote_summary(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # F) “Which Day?” step = collect_day_option
            if step == "collect_day_option" and payload_lower in ["day_today", "day_tomorrow", "day_pick"]:
                if payload_lower == "day_today":
                    today_str = datetime.now().strftime("%d-%m-%Y")
                    state["appointment_date"] = today_str
                    state["step"] = "collect_time_option"
                    set_user_state(prefix, from_number, state)
                    send_time_selection_prompt(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID"),
                        chosen_date=today_str
                    )
                    return

                if payload_lower == "day_tomorrow":
                    tomorrow = datetime.now() + timedelta(days=1)
                    tomorrow_str = tomorrow.strftime("%d-%m-%Y")
                    state["appointment_date"] = tomorrow_str
                    state["step"] = "collect_time_option"
                    set_user_state(prefix, from_number, state)
                    send_time_selection_prompt(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID"),
                        chosen_date=tomorrow_str
                    )
                    return

                if payload_lower == "day_pick":
                    state["step"] = "collect_date_option"
                    set_user_state(prefix, from_number, state)
                    send_upcoming_dates_list(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

            # G) “Which Time?” step = collect_time_option
            if step == "collect_time_option" and payload_lower in ["time_morning", "time_afternoon", "time_evening"]:
                if payload_lower == "time_morning":
                    state["appointment_time"] = "10:00"
                elif payload_lower == "time_afternoon":
                    state["appointment_time"] = "12:00"
                else:  # "time_evening"
                    state["appointment_time"] = "18:00"

                # Move on to final details
                state["step"] = "collect_final_details"
                set_user_state(prefix, from_number, state)
                send_text_message(
                    to=from_number,
                    body=(
                        "Great! Please reply in one sentence using **this format, separated by commas**:\n\n"
                        "Vehicle Model, Vehicle Number, On-site Location\n"
                        "For example:\n"
                        "**Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559**"
                    )
                )
                return

            # H) “Yes”/“No” on luxury-fee prompt when step == "check_luxury"
            if step == "check_luxury" and payload_lower in ["yes", "no", "luxury_yes", "luxury_no"]:
                if payload_lower in ["yes", "luxury_yes"]:
                    state["continental"] = "luxury_yes"
                else:
                    state["continental"] = "luxury_no"
                state["step"] = "select_location"
                set_user_state(prefix, from_number, state)
                send_location_selection(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # I) Unhandled button payload
            print(f"[DEBUG] Unhandled BUTTON/BR payload: '{payload_lower}' (step={step})")
            send_text_message(
                to=from_number,
                body="Sorry, I didn’t understand that button. Type 'reset' to start over."
            )
            return

    # ----------------------------------------------------------------
    # 2) Handle interactive LIST replies
    # ----------------------------------------------------------------
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_car_fumigation_flow: LIST payload='{selected_id}' from {from_number}")

        state = user_state or {}
        step = state.get("step", "")

        # A) Handling FAQ list selection was covered above

        # B) step == "choose_service": Pest Control Services list
        if step == "choose_service":
            if selected_id == "car_fumigation":
                state.clear()
                state["step"] = "select_pest_type"
                set_user_state(prefix, from_number, state)
                send_pest_type_list(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return
            else:
                send_text_message(
                    to=from_number,
                    body="Sorry, that service is not available yet. Type 'reset' to start over."
                )
                return

        # C) step == "select_pest_type": Pest Type list
        if step == "select_pest_type":
            if selected_id == "other_pest":
                state["step"] = "collect_other_pest_text"
                set_user_state(prefix, from_number, state)
                send_text_message(
                    to=from_number,
                    body="Please type in which pest you saw in your vehicle."
                )
                return
            else:
                state["pest_type"] = selected_id
                state["step"] = "select_vehicle_type"
                set_user_state(prefix, from_number, state)
                send_vehicle_type_list(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # D) step == "select_vehicle_type": Vehicle Type list
        if step == "select_vehicle_type":
            if selected_id == "vehicle_others":
                state["step"] = "collect_other_vehicle_text"
                state["vehicle"] = selected_id
                state["manual_quote"] = True
                set_user_state(prefix, from_number, state)
                send_text_message(
                    to=from_number,
                    body="Please type in your vehicle model (e.g. Toyota Hiace, Proton X70, etc.)."
                )
                return

            elif selected_id == "vehicle_ultra_luxury":
                state["step"] = "select_location"
                state["vehicle"] = selected_id
                state["manual_quote"] = True
                set_user_state(prefix, from_number, state)
                send_location_selection(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            else:
                state["vehicle"] = selected_id
                state["step"] = "check_luxury"
                state["manual_quote"] = False
                set_user_state(prefix, from_number, state)
                send_cfadditionalfee_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # E) step == "select_location": Service Zone list
        if step == "select_location":
            state["location"] = selected_id
            state["step"] = "show_quote_summary"
            set_user_state(prefix, from_number, state)
            send_quote_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # F) step == "collect_date_option": user selected from upcoming dates
        if step == "collect_date_option":
            if selected_id.startswith("date_"):
                # Extract date part: "date_09-06-2025" → "09-06-2025"
                _, date_str = selected_id.split("_", 1)
                state["appointment_date"] = date_str
                state["step"] = "collect_time_option"
                set_user_state(prefix, from_number, state)
                send_time_selection_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
                    chosen_date=date_str
                )
                return

            elif selected_id == "other_dates":
                state["step"] = "collect_custom_date_text"
                set_user_state(prefix, from_number, state)
                send_text_message(
                    to=from_number,
                    body=(
                        "Please type your preferred date in `DD-MM-YYYY` format.  \n"
                        "For example: `11-06-2025`."
                    )
                )
                return

        # G) step == "car_faq": already handled above

        # Otherwise, unexpected step
        print(f"[DEBUG] LIST reply received but step='{step}' is unexpected")
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ----------------------------------------------------------------
    # 3) Handle plain-text replies at “collect_*” steps
    # ----------------------------------------------------------------
    if msg_type == "text":
        state = user_state or {}
        step = state.get("step", "")
        text_body = message["text"]["body"].strip()
        print(f"[DEBUG] handle_car_fumigation_flow: TEXT at step='{step}': '{text_body}' from {from_number}")

        # A) collect_other_pest_text
        if step == "collect_other_pest_text":
            state["pest_type"] = text_body
            state["step"] = "select_vehicle_type"
            set_user_state(prefix, from_number, state)
            send_vehicle_type_list(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) collect_other_vehicle_text
        if step == "collect_other_vehicle_text":
            state["vehicle_model"] = text_body
            state["step"] = "select_location"
            set_user_state(prefix, from_number, state)
            send_location_selection(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # C) collect_custom_date_text (user enters DD-MM-YYYY)
        if step == "collect_custom_date_text":
            user_date = text_body
            try:
                # Validate DD-MM-YYYY
                parsed = datetime.strptime(user_date, "%d-%m-%Y")
                state["appointment_date"] = user_date
                state["step"] = "collect_time_option"
                set_user_state(prefix, from_number, state)
                send_time_selection_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
                    chosen_date=user_date
                )
            except ValueError:
                send_text_message(
                    to=from_number,
                    body="Sorry, I couldn’t parse that date. Please use `DD-MM-YYYY`, e.g. `11-06-2025`."
                )
            return

        # D) collect_date_option: user typed a date instead of tapping a list item
        if step == "collect_date_option":
            user_date = text_body
            try:
                # Try parsing DD-MM-YYYY
                parsed = datetime.strptime(user_date, "%d-%m-%Y")
                # If valid, store and move to time selection
                state["appointment_date"] = user_date
                state["step"] = "collect_time_option"
                set_user_state(prefix, from_number, state)
                send_time_selection_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
                    chosen_date=user_date
                )
            except ValueError:
                send_text_message(
                    to=from_number,
                    body=(
                        "Sorry, I couldn’t parse that date. Please choose one of the listed dates "
                        "or type a valid date in `DD-MM-YYYY`, e.g. `09-06-2025`."
                    )
                )
            return

        # E) collect_custom_time_text (user enters free-form time)
        if step == "collect_custom_time_text":
            user_time = text_body.strip().upper().replace(" ", "")
            parsed_time = None

            # Try parsing “HH:MM” (24-hour)
            try:
                parsed_time = datetime.strptime(user_time, "%H:%M").time()
            except Exception:
                # Try parsing “H:MMAM/PM” or “HH:MMAM/PM”
                for fmt in ("%I:%M%p", "%I:%M%P"):
                    try:
                        parsed_time = datetime.strptime(user_time, fmt).time()
                        break
                    except Exception:
                        continue

            if parsed_time is None:
                send_text_message(
                    to=from_number,
                    body="Sorry, I couldn’t parse that time. Please send `18:30` or `6:30pm`."
                )
                return

            # If parsing succeeded:
            state["appointment_time"] = parsed_time.strftime("%H:%M")
            state["step"] = "collect_final_details"
            set_user_state(prefix, from_number, state)
            send_text_message(
                to=from_number,
                body=(
                    "Great! Please reply in one sentence using **this format, separated by commas**:\n\n"
                    "Vehicle Model, Vehicle Number, On-site Location\n"
                    "For example:\n"
                    "**Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559**"
                )
            )
            return

        # F) collect_time_option: user typed a free-form time
        if step == "collect_time_option":
            # Attempt to parse free-form time exactly as above
            user_time = text_body.strip().upper().replace(" ", "")
            parsed_time = None
            try:
                parsed_time = datetime.strptime(user_time, "%H:%M").time()
            except Exception:
                for fmt in ("%I:%M%p", "%I:%M%P"):
                    try:
                        parsed_time = datetime.strptime(user_time, fmt).time()
                        break
                    except Exception:
                        continue

            if parsed_time:
                # Accept it and move to final details
                state["appointment_time"] = parsed_time.strftime("%H:%M")
                state["step"] = "collect_final_details"
                set_user_state(prefix, from_number, state)
                send_text_message(
                    to=from_number,
                    body=(
                        "Great! Please reply in one sentence using **this format, separated by commas**:\n\n"
                        "Vehicle Model, Vehicle Number, On-site Location\n"
                        "For example:\n"
                        "**Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559**"
                    )
                )
                return
            else:
                # If parsing fails, re-prompt time selection
                send_text_message(
                    to=from_number,
                    body="Sorry, I couldn’t parse that time. Please type something like `18:30` or `6:30pm`, or tap one of the buttons."
                )
                return

        # G) collect_final_details (single comma-separated line)
        if step == "collect_final_details":
            parts = [p.strip() for p in text_body.split(",")]
            if len(parts) != 3:
                send_text_message(
                    to=from_number,
                    body=(
                        "Sorry, I couldn’t parse that.  \n"
                        "Please reply in one sentence using **this format, separated by commas**:\n\n"
                        "Vehicle Model, Vehicle Number, On-site Location\n"
                        "For example:\n"
                        "**Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559**"
                    )
                )
                return

            vehicle_model   = parts[0]
            vehicle_number  = parts[1]
            parking_address = parts[2]

            state["vehicle_model"]   = vehicle_model
            state["vehicle_number"]  = vehicle_number
            state["parking_address"] = parking_address

            # Fetch needed fields from state
            pest_encountered = state.get("pest_type", "N/A")
            total_quote = state.get("computed_quote", "N/A")
            appointment_date = state.get("appointment_date", "")
            appointment_time = state.get("appointment_time", "")

            # Clear Redis state now that we have all info
            clear_user_state(prefix, from_number)

            # Send confirmation back to the customer with full summary
            send_text_message(
                to=from_number,
                body=(
                    "Thank you! Your appointment request has been received.\n\n"
                    "Details provided:\n\n"
                    f"• Pest Encounter: {pest_encountered}\n"
                    f"• Estimated Quote: ${total_quote}\n"
                    f"• Date: {appointment_date}\n"
                    f"• Time: {appointment_time}\n"
                    f"• Vehicle Model: {vehicle_model}\n"
                    f"• Vehicle Number: {vehicle_number}\n"
                    f"• Parking Address: {parking_address}\n\n"
                    "We're connecting you to a live agent now. Meanwhile, you may review our Car Fumigation FAQ:"
                )
            )
            # Show FAQ for any last-minute questions
            send_car_fumigation_faq(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )

            # Alert internal team with all details
            alert_body = (
                "🚨 New Car Fumigation Booking 🚨\n\n"
                f"Client Phone Number: +{from_number}\n"
                f"Pest Encountered: {pest_encountered}\n"
                f"Total Estimated Quote: ${total_quote}\n"
                f"Date/Time: {appointment_date} {appointment_time}\n"
                f"Vehicle Model: {vehicle_model}\n"
                f"Vehicle Number: {vehicle_number}\n"
                f"Parking Address: {parking_address}"
            )
            for admin in ALERT_NUMBERS:
                send_text_message(to=admin, body=alert_body)

            return

        # H) any other text outside expected steps
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ----------------------------------------------------------------
    # 4) Fallback for any other payload types
    # ----------------------------------------------------------------
    print(f"[DEBUG] handle_car_fumigation_flow: Unsupported msg_type='{msg_type}'")
    send_text_message(
        to=from_number,
        body="Sorry, I can’t handle that type of message. Type 'reset' to start over."
    )
    return
