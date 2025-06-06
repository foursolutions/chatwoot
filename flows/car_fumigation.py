import os
from datetime import datetime, timedelta

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_interactive_message,
    send_template_message,
)

prefix = "carfum"


# =====================================================================
# 1) Send the Pest Control Services List (interactive list)
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
                        "title": "Services",
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
    print(f"[DEBUG] send_pest_control_list → 1MSG response: {resp}")


# =====================================================================
# 2) Car Fumigation Menu → Template `car_fum_menu`
# =====================================================================
def send_car_fum_menu(to: str, phone_number_id: str):
    resp = send_template_message(
        to=to,
        template_name="car_fum_menu",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_menu → 1MSG response: {resp}")


# =====================================================================
# 3) Car Fumigation Info / Quote Options → Template `car_fum_quote_options`
# =====================================================================
def send_car_fum_quote_options(to: str, phone_number_id: str):
    resp = send_template_message(
        to=to,
        template_name="car_fum_quote_options",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_quote_options → 1MSG response: {resp}")


# =====================================================================
# 4) “Select Pest Type” → Interactive List
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
    print(f"[DEBUG] send_pest_type_list → 1MSG response: {resp}")


# =====================================================================
# 5) “Select Vehicle Type” → Interactive List
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
                        "title": "Vehicle Categories",
                        "rows": [
                            {"id": "vehicle_sedan",  "title": "Sedan 🚗",   "description": ""},
                            {"id": "vehicle_suv",    "title": "SUV 🚙",      "description": ""},
                            {"id": "vehicle_mpv",    "title": "MPV 🚐",      "description": ""},
                            {"id": "vehicle_vans",   "title": "Van 🚛",      "description": ""},
                            {"id": "vehicle_others", "title": "Others 🚘",   "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_vehicle_type_list → 1MSG response: {resp}")


# =====================================================================
# 6) “Additional Care Fee” → Quick-Reply Buttons (Luxury-Brand Prompt)
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
    print(f"[DEBUG] send_cfadditionalfee_prompt → 1MSG response: {resp}")


# =====================================================================
# 7) Utility: Send a dynamic list of the next 7 dates
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
    print(f"[DEBUG] send_upcoming_dates_list → 1MSG response: {resp}")


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
            "header": {"type": "text", "text": "Select Your Location"},
            "body": {"text": "Where would you like us to service your vehicle?"},
            "footer": {"text": "Tap to choose"},
            "action": {
                "button": "Select Location",
                "sections": [
                    {
                        "title": "Areas",
                        "rows": [
                            {"id": "location_north",     "title": "North",        "description": ""},
                            {"id": "location_northeast", "title": "Northeast",    "description": ""},
                            {"id": "location_east",      "title": "East",         "description": ""},
                            {"id": "location_central",   "title": "Central",      "description": ""},
                            {"id": "location_west",      "title": "West",         "description": ""},
                            {"id": "location_south",     "title": "South",        "description": ""},
                            {"id": "location_sentosa",   "title": "Sentosa",      "description": ""}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_location_selection → 1MSG response: {resp}")


# =====================================================================
# 9) “Which Day?” → Interactive Button Prompt (max 3 buttons)
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
    print(f"[DEBUG] send_day_selection_prompt → 1MSG response: {resp}")


# =====================================================================
# 10) “Which Time?” → Interactive Button Prompt (max 3 buttons)
# =====================================================================
def send_time_selection_prompt(to: str, phone_number_id: str, chosen_date: str):
    state = get_user_state(prefix, to) or {}
    state["appointment_date"] = chosen_date
    set_user_state(prefix, to, state)

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
    print(f"[DEBUG] send_time_selection_prompt → 1MSG response: {resp}")


# =====================================================================
# 11) “Quote Summary” → Interactive Button Template
# =====================================================================
def send_quote_summary(to: str, phone_number_id: str):
    state = get_user_state(prefix, to) or {}

    if state.get("manual_quote", False):
        # User selected “Others” or “Require agent quote” category
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
        # Compute base, additional fee, and location charge
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
        set_user_state(prefix, to, state)

        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            f"- Car Model Type Pricing: ${base_quote}\n"
            f"- Additional Care Fee: ${additional_fee}\n"
            f"- Location Charge: ${location_charge}\n\n"
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
    print(f"[DEBUG] send_quote_summary → 1MSG response: {resp}")


# =====================================================================
# 12) Car Fumigation FAQ Interactive List
# =====================================================================
def send_car_fumigation_faq(to: str, phone_number_id: str):
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Car Fumigation FAQ"},
            "body": {"text": "Select a FAQ question:"},
            "footer": {"text": "Tap an option"},
            "action": {
                "button": "Select FAQ",
                "sections": [
                    {
                        "title": "FAQ Questions",
                        "rows": [
                            {"id": "cfq_safe",        "title": "Is it safe? Kids/Pets",   "description": "Safety with HACCP chemicals"},
                            {"id": "cfq_included",    "title": "Service Details",          "description": "What's included in our service?"},
                            {"id": "cfq_warranty",    "title": "Our Warranty",            "description": "Warranty information"},
                            {"id": "cfq_preparation", "title": "Preparation",             "description": "What to prepare before service"},
                            {"id": "cfq_duration",    "title": "Service Duration",        "description": "How long the service takes"},
                            {"id": "cfq_payment",     "title": "Payment Options",         "description": "Payment methods accepted"}
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_car_fumigation_faq → 1MSG response: {resp}")


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
            "We provide a 30-day coverage warranty. If any live pests return within this window, "
            "we will re-treat your vehicle at no additional cost."
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
# 13) Universal flow‐handler: handle_car_fumigation_flow
# =====================================================================
def handle_car_fumigation_flow(from_number: str, message: dict, user_state: dict):
    """
    1) Determine whether this is:
       - an interactive list reply (message["type"] == "interactive" with "list_reply"),
       - a quick‐reply button (message["type"] == "button" or "button_reply"),
       - or plain text (for “collect_*” steps).
    2) Extract payload / ID, compare to current user_state["step"].
    3) Update Redis state accordingly.
    4) Call next send_*() function to continue the flow.
    """
    prefix = "carfum"
    msg_type = message.get("type", "")  # could be "text", "button", "interactive", "button_reply", etc.

    # ─── 0) FIRST: Handle the “choose_service” interactive LIST reply ───
    state = user_state or {}
    step = state.get("step", "")

    if step == "choose_service" and msg_type == "interactive" and "list_reply" in message:
        # Extract which service the user selected from the list
        selected_id = message["list_reply"]["id"]
        print(f"[DEBUG] handle_car_fumigation_flow: LIST payload='{selected_id}' from {from_number}")

        if selected_id == "car_fumigation":
            # User chose Car Fumigation → send the Car Fumigation menu
            state["step"] = "car_menu"
            set_user_state(prefix, from_number, state)
            send_car_fum_menu(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # If you want to support other pest services here (bedbugs, roaches_ants, etc.),
        # you can add additional branches such as:
        #
        # elif selected_id == "bedbugs":
        #     state["step"] = "bedbug_flow"
        #     set_user_state(prefix, from_number, state)
        #     send_bedbug_menu(...)
        #     return
        #
        # In this example, we only route “car_fumigation” to the car‐specific menu.

        # If the ID doesn't match a known service, send a fallback
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t recognize that service. Please tap “Need help on Pest!” to restart."
        )
        clear_user_state(prefix, from_number)
        return

    # ─── 1) FAQ Handling: if step == "car_faq", handle FAQ replies first ───
    # A) FAQ replies from quick‐reply BUTTON payloads
    if step == "car_faq" and msg_type in ["button", "button_reply"]:
        payload = ""
        inner_type = message.get("type", "")
        # 1MSG “button” → top‐level "body"
        if inner_type == "button":
            payload = message.get("body", "").strip()
        # 360dialog “button_reply” → nested msg["button"]["payload"]
        elif inner_type == "button_reply" and "button" in message:
            payload = message["button"].get("payload", "").strip()

        if payload.startswith("cfq_"):
            process_car_fumigation_faq_response(from_number, payload)
            # Re‐show FAQ list so user can select again
            send_car_fumigation_faq(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # B) FAQ replies from interactive LIST (list_reply)
    if step == "car_faq" and msg_type == "interactive" and "list_reply" in message:
        selected_id = message["list_reply"]["id"]
        if selected_id.startswith("cfq_"):
            process_car_fumigation_faq_response(from_number, selected_id)
            # Re‐show FAQ list
            send_car_fumigation_faq(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # ─── 2) Handle quick‐reply BUTTONS (non‐FAQ) ───────────────────────────
    if msg_type in ["button", "button_reply"]:
        # Extract payload for quick‐reply buttons
        payload = ""
        inner_type = message.get("type", "")
        if inner_type == "button":
            payload = message.get("body", "").strip()
        elif inner_type == "button_reply" and "button" in message:
            payload = message["button"].get("payload", "").strip()

        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_car_fumigation_flow: BUTTON payload='{payload_lower}' from {from_number}")

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
                # This function is not defined here; replace with your actual main-menu sender
                send_text_message(
                    to=from_number,
                    body="Returning you to the main menu. Please tap 'Need help on Pest!' or 'Need help on Mold!'."
                )
                return

            # D) “Book Now” on quote summary → Ask “Which Day?”
            if step == "show_quote_summary" and payload_lower in ["book_appointment", "car_fum_confirm_yes", "yes"]:
                state["step"] = "collect_day_option"
                set_user_state(prefix, from_number, state)
                send_day_selection_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # E) “No” on final quote summary → back to quote summary
            if step == "show_quote_summary" and payload_lower in ["return_to_quote", "car_fum_confirm_no", "no"]:
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
                    state["step"] = "pick_date"
                    set_user_state(prefix, from_number, state)
                    send_upcoming_dates_list(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

            # G) “Which Time?” step = collect_time_option
            if step == "collect_time_option" and payload_lower in ["time_morning", "time_afternoon", "time_evening"]:
                selected_time = {
                    "time_morning": "10:00AM - 12:00PM",
                    "time_afternoon": "12:00PM - 6:00PM",
                    "time_evening": "6:00PM - 11:59PM"
                }[payload_lower]
                state["appointment_time"] = selected_time
                state["step"] = "select_location"
                set_user_state(prefix, from_number, state)
                send_location_selection(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # H) “Select Location” step = select_location handling
            if step == "select_location":
                # In case you sent a button‐style location prompt, handle it here
                # But we used a LIST for location, so “select_location” via interactive LIST will appear below
                pass

    # ─── 3) LIST‐REPLY (“interactive” with “list_reply”) for deeper steps ───
    if msg_type == "interactive" and "list_reply" in message:
        selected_id = message["list_reply"]["id"]
        state = user_state or {}
        step = state.get("step", "")

        # A) “Which Pest Type?” step = select_pest_type
        if step == "select_pest_type":
            # Save pest type
            state["pest_type"] = selected_id  # e.g. “cockroach”, “ants”, etc.
            state["step"] = "select_vehicle"
            set_user_state(prefix, from_number, state)
            send_vehicle_type_list(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) “Select Vehicle Type” step = select_vehicle
        if step == "select_vehicle":
            state["vehicle"] = selected_id  # e.g. “vehicle_sedan”, “vehicle_suv”, etc.
            # If “Others”, mark manual_quote and jump to quote summary
            if selected_id == "vehicle_others":
                state["manual_quote"] = True
            state["step"] = "select_additional_fee"
            set_user_state(prefix, from_number, state)
            send_cfadditionalfee_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # C) “Which Day?” step = pick_date
        if step == "pick_date":
            if selected_id.startswith("date_"):
                # Extract the date string from “date_DD-MM-YYYY”
                chosen_date = selected_id.replace("date_", "")
                state["appointment_date"] = chosen_date
                state["step"] = "collect_time_option"
                set_user_state(prefix, from_number, state)
                send_time_selection_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
                    chosen_date=chosen_date
                )
                return
            elif selected_id == "other_dates":
                # Let user type a date manually
                state["step"] = "manual_date_entry"
                set_user_state(prefix, from_number, state)
                send_text_message(
                    to=from_number,
                    body="Please type your preferred date in DD-MM-YYYY format."
                )
                return

        # D) “Select Location” step = select_location
        if step == "select_location":
            state["location"] = selected_id  # e.g. “location_north”, etc.
            state["step"] = "show_quote_summary"
            set_user_state(prefix, from_number, state)
            send_quote_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # ─── 4) TEXT (manual entry) for steps that require free‐form input ───
    if msg_type == "text":
        text_body = message["text"]["body"].strip().lower()
        state = user_state or {}
        step = state.get("step", "")

        # A) If user is manually entering a date
        if step == "manual_date_entry":
            # Validate DD-MM-YYYY
            try:
                datetime.strptime(text_body, "%d-%m-%Y")
                state["appointment_date"] = text_body
                state["step"] = "collect_time_option"
                set_user_state(prefix, from_number, state)
                send_time_selection_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID"),
                    chosen_date=text_body
                )
            except ValueError:
                send_text_message(
                    to=from_number,
                    body="That date format wasn’t recognized. Please enter in DD-MM-YYYY format."
                )
            return

        # B) If user types a custom time (e.g., “18:30” or “6:30pm”)
        if step == "collect_time_option":
            # Very basic pattern: accept anything that looks like “hh:mm”
            if ":" in text_body:
                state["appointment_time"] = text_body
                state["step"] = "select_location"
                set_user_state(prefix, from_number, state)
                send_location_selection(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
            else:
                send_text_message(
                    to=from_number,
                    body="Please type a valid time (e.g. “18:30” or “6:30pm”), or tap one of the buttons above."
                )
            return

        # C) If free‐form “return to main menu” typed
        if text_body in ["return to main menu", "main menu", "menu", "restart"]:
            clear_user_state(prefix, from_number)
            send_text_message(
                to=from_number,
                body="Returning you to the main menu. Please tap 'Need help on Pest!' or 'Need help on Mold!'."
            )
            return

        # Otherwise, catch‐all
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Please use the buttons or type “return to main menu”."
        )
        return

    # ─── 5) Fallback for any unmatched case ───────────────────────────────
    print(f"[DEBUG] handle_car_fumigation_flow: unsupported msg_type='{msg_type}', step='{step}' from {from_number}.")
    send_text_message(
        to=from_number,
        body="Sorry, I can’t handle that type of message right now. Type “reset” to start over."
    )
    clear_user_state(prefix, from_number)

