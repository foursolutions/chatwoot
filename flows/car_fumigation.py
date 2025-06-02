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

# ------------------------------------------------------------------------------
# 1) Main Menu (Template)
# ------------------------------------------------------------------------------
def send_main_menu(to: str, phone_number_id: str):
    """
    Sends the top-level main menu template (main_menu_v2).
    This template has one body placeholder {{1}}, so we must supply exactly one non-empty string.
    """
    greeting_name = "there"
    resp = send_template_message(
        to=to,
        template_name="main_menu_v2",
        template_params=[greeting_name]
    )
    print(f"[DEBUG] send_main_menu → 360dialog response: {resp}")


# ------------------------------------------------------------------------------
# 2) Pest Control Services → Interactive List
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# 3) Car Fumigation Menu → Template `car_fum_menu`
# ------------------------------------------------------------------------------
def send_car_fum_menu(to: str, phone_number_id: str):
    """
    Sends the `car_fum_menu` template with quick-reply button IDs:
      - "car_fum_quote"     (Request a Quotation)
      - "car_fum_info"      (More Info on Service)
      - "return_main_menu"  (Return to Main Menu)
    """
    resp = send_template_message(
        to=to,
        template_name="car_fum_menu",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_menu → 360dialog response: {resp}")


# ------------------------------------------------------------------------------
# 4) Car Fumigation Info / Quote Options → Template `car_fum_quote_options`
# ------------------------------------------------------------------------------
def send_car_fum_quote_options(to: str, phone_number_id: str):
    """
    Sends the `car_fum_quote_options` template with quick-reply buttons:
      - "car_fum_book"
      - "car_fum_info"
      - "return_main_menu"
    (Not used directly in this flow; stubbed for completeness.)
    """
    resp = send_template_message(
        to=to,
        template_name="car_fum_quote_options",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_quote_options → 360dialog response: {resp}")


# ------------------------------------------------------------------------------
# 5) “Select Pest Type” → Interactive List
# ------------------------------------------------------------------------------
def send_pest_type_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of pest types inside the vehicle:
      - cockroach      (id="cockroach")
      - ants           (id="ants")
      - lizards        (id="lizards")
      - other_pest     (id="other_pest")
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


# ------------------------------------------------------------------------------
# 6) “Select Vehicle Type” → Interactive List
# ------------------------------------------------------------------------------
def send_vehicle_type_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of vehicle types with updated IDs:
      - Sedan/Hatchback          (id="vehicle_sedan")
      - SUV                      (id="vehicle_suv")
      - MPV                      (id="vehicle_mpv")
      - Vans/Lorries             (id="vehicle_vans")
      - Super/Luxury Cars        (id="vehicle_ultra_luxury")
      - Others                   (id="vehicle_others")
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


# ------------------------------------------------------------------------------
# 7) “Additional Care Fee” → Quick-Reply Buttons (Luxury-Brand Prompt)
# ------------------------------------------------------------------------------
def send_cfadditionalfee_prompt(to: str, phone_number_id: str):
    """
    Sends a yes/no button prompt asking if the vehicle is a luxury brand,
    which would incur a $10 add-on fee.
    """
    text = (
        "Does your vehicle manufacturer fall under one of the options below?\n\n"
        "1) Mercedes-Benz\n"
        "2) BMW\n"
        "3) Audi\n"
        "4) Lexus\n"
        "5) Porsche\n"
        "6) Jaguar\n"
        "7) Tesla\n"
        "8) Range Rover\n\n"
        "These vehicle brands require additional care while servicing.\n"
        "Please select either Yes or No."
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


# ------------------------------------------------------------------------------
# 8) “Select Location” → Interactive List
# ------------------------------------------------------------------------------
def send_location_selection(to: str, phone_number_id: str):
    """
    Sends an interactive list of service zones using the given format:
      - North               (id="location_north")       – $20
      - North-East          (id="location_northeast")   – $20
      - Central             (id="location_central")     – $25
      - East                (id="location_east")        – $20
      - West                (id="location_west")        – $25
      - South               (id="location_south")       – $25
      - Sentosa & Restricted (id="location_sentosa")    – $40
    """
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


# ------------------------------------------------------------------------------
# 9) “Which Day?” → Interactive Button Prompt
# ------------------------------------------------------------------------------
def send_day_selection_prompt(to: str, phone_number_id: str):
    """
    Step 1: Ask the user which day they want:
      • Today       (id="day_today")
      • Tomorrow    (id="day_tomorrow")
      • Pick a Date (id="day_pick")
    This is an "interactive" button message (no 360dialog template required).
    """
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


# ------------------------------------------------------------------------------
# 10) “Which Time?” → Interactive Button Prompt (max. 3 buttons)
# ------------------------------------------------------------------------------
def send_time_selection_prompt(to: str, phone_number_id: str, chosen_date: str):
    """
    Step 2: Ask the user which time slot or a custom time.
    `chosen_date` is either "today", "tomorrow" or a user-typed "DD-MM-YYYY".
    We store it in state so we can attach it later.
    """
    # Store the chosen_date in state
    state = get_user_state("carfum", to) or {}
    state["appointment_date"] = chosen_date
    set_user_state("carfum", to, state)

    # Build a 3-button prompt for time (WhatsApp allows max 3 buttons)
    text = (
        f"You chose *{chosen_date}* for your appointment.\n\n"
        "What time of day works best?\n"
        "• Morning (09:00–12:00)\n"
        "• Afternoon (12:00–17:00)\n"
        "• Or enter a custom time (e.g. \"18:30\" or \"6:30pm\")."
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
                    {"type": "reply", "reply": {"id": "time_custom",    "title": "Enter Time"}}
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_time_selection_prompt → {resp}")


# ------------------------------------------------------------------------------
# 11) “Quote Summary” → Interactive Button Template
# ------------------------------------------------------------------------------
def send_quote_summary(to: str, phone_number_id: str):
    """
    Builds the quote summary based on everything in user_state (stored in Redis).
    - If the user chose an “ultra_luxury” or “vehicle_others” model, we mark manual quote.
    - Otherwise, we compute:
        • base_quote       (vehicle pricing)
        • additional_fee   ($10 if luxury_yes)
        • location_charge  (based on zone)
    Then we send an interactive button template with three quick-reply options:
      - "book_appointment"
      - "fumigation_faq"
      - "return_main_menu"
    """
    state = get_user_state("carfum", to) or {}

    if state.get("manual_quote", False):
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Below is the estimated breakdown of your quotation:\n\n"
            "- Car Model Type Pricing: Customized Quote Required\n"
            "- Additional Care Fee: $0\n"
            "- On-site Service Charge: $0\n\n"
            "Estimated Total: Your vehicle or service request requires a customized quotation. "
            "Please allow an agent to assist you with this.\n\n"
            "Please select an option below:"
        )
    else:
        # Determine base_quote from vehicle_type
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

        # Determine additional_fee if luxury
        additional_fee = 10 if state.get("continental") == "luxury_yes" else 0

        # Determine location_charge from chosen zone
        loc = state.get("location", "")
        if loc in ["location_north", "location_northeast", "location_east"]:
            location_charge = 20
        elif loc in ["location_central", "location_west", "location_south"]:
            location_charge = 25
        elif loc == "location_sentosa":
            location_charge = 40
        else:
            location_charge = 0

        # Compute total
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

    # Build the interactive button payload
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


# ------------------------------------------------------------------------------
# 12) Universal flow-handler: handle_car_fumigation_flow
# ------------------------------------------------------------------------------
def handle_car_fumigation_flow(from_number: str, message: dict, user_state: dict):
    """
    1) Determine whether this is a quick-reply button (message["type"] == "button" or nested "interactive.button_reply"),
       an interactive list reply, or plain text (for "collect_*" steps).
    2) Extract the payload/text, compare to the current `user_state["step"]`.
    3) Update Redis state accordingly.
    4) Call the next send_*() function to continue the flow.
    """
    prefix = "carfum"
    msg_type = message.get("type")  # "text", "button", or "interactive"

    # ─── Helper to extract quick-reply payload ───
    def extract_button_payload(msg: dict) -> str:
        """
        360dialog may send quick-reply buttons under:
          - msg["type"] == "button" → msg["button"]["payload"]
          - msg["type"] == "interactive" and msg["interactive"]["type"] == "button_reply" → msg["interactive"]["button_reply"]["id"]
        """
        if msg.get("type") == "button":
            return msg["button"]["payload"]
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"]["id"]
        return ""

    # ─── 1) Handle quick-reply BUTTONS (either "button" or "interactive.button_reply") ───
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_car_fumigation_flow: BUTTON/BR payload='{payload_lower}' from {from_number}")

            state = user_state or {}
            step = state.get("step")

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

            # B) “More Info on Service” at any point
            if payload_lower in ["more info on service", "fumigation_faq"]:
                send_text_message(
                    to=from_number,
                    body=(
                        "Our car fumigation service uses non-oily fogging. "
                        "Prices start at SGD 50 for a basic treatment. "
                        "Type 'reset' to go back anytime."
                    )
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
                    state["step"] = "collect_custom_date_text"
                    set_user_state(prefix, from_number, state)
                    send_text_message(
                        to=from_number,
                        body=(
                            "Please type your preferred date in `DD-MM-YYYY` format.  \n"
                            "For example: `11-06-2025`"
                        )
                    )
                    return

            # G) “Which Time?” step = collect_time_option
            if step == "collect_time_option" and payload_lower in ["time_morning", "time_afternoon", "time_custom"]:
                if payload_lower == "time_morning":
                    state["appointment_time"] = "09:00"
                elif payload_lower == "time_afternoon":
                    state["appointment_time"] = "13:00"
                else:  # "time_custom"
                    state["step"] = "collect_custom_time_text"
                    set_user_state(prefix, from_number, state)
                    send_text_message(
                        to=from_number,
                        body=(
                            "Please type your preferred time in HH:MM (24-hour) or HH:MMam/pm (12-hour).  \n"
                            "For example: `18:30` or `6:30pm`"
                        )
                    )
                    return

                # If they tapped one of the two preset slots (Morning or Afternoon):
                state["step"] = "collect_final_details"
                set_user_state(prefix, from_number, state)
                send_text_message(
                    to=from_number,
                    body=(
                        "Great! Please provide all three items in one sentence, separated by commas:\n\n"
                        "Vehicle Model, Vehicle Number, On-site Location  \n"
                        "For example:\n"
                        "`Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559`"
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

    # ─── 2) Handle interactive LIST replies ───
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_car_fumigation_flow: LIST payload='{selected_id}' from {from_number}")

        state = user_state or {}
        step = state.get("step")

        # A) step == "choose_service": Pest Control Services list
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

        # B) step == "select_pest_type": Pest Type list
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

        # C) step == "select_vehicle_type": Vehicle Type list
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
                # One of Sedan/SUV/MPV/Vans → ask luxury-fee question
                state["vehicle"] = selected_id
                state["step"] = "check_luxury"
                state["manual_quote"] = False
                set_user_state(prefix, from_number, state)
                send_cfadditionalfee_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # D) step == "select_location": Service Zone list
        if step == "select_location":
            state["location"] = selected_id
            state["step"] = "show_quote_summary"
            set_user_state(prefix, from_number, state)
            send_quote_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # Otherwise, unexpected step
        print(f"[DEBUG] LIST reply received but step='{step}' is unexpected")
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── 3) Handle plain-text replies at “collect_*” steps ───
    if msg_type == "text":
        state = user_state or {}
        step = state.get("step")
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
                # If successful, store in that exact format
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

        # D) collect_custom_time_text (user enters free-form time)
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
                    "Great! Please provide all three items in one sentence, separated by commas:\n\n"
                    "Vehicle Model, Vehicle Number, On-site Location  \n"
                    "For example:\n"
                    "`Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559`"
                )
            )
            return

        # E) collect_final_details (single comma-separated line)
        if step == "collect_final_details":
            parts = [p.strip() for p in text_body.split(",")]
            if len(parts) != 3:
                # If they didn’t send exactly three items, re-prompt:
                send_text_message(
                    to=from_number,
                    body=(
                        "Sorry, I couldn’t parse that.  \n"
                        "Please send *all three* items in one line, separated by commas:\n\n"
                        "Vehicle Model, Vehicle Number, On-site Location  \n"
                        "For example:\n"
                        "`Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559`"
                    )
                )
                return

            vehicle_model   = parts[0]
            vehicle_number  = parts[1]
            parking_address = parts[2]

            state["vehicle_model"]   = vehicle_model
            state["vehicle_number"]  = vehicle_number
            state["parking_address"] = parking_address

            # Clear Redis state now that we have all info
            clear_user_state(prefix, from_number)

            # Thank them and connect to agent + FAQ:
            send_text_message(
                to=from_number,
                body=(
                    f"Thank you. Your appointment is set for "
                    f"{state['appointment_date']} at {state['appointment_time']}.\n\n"
                    f"• Vehicle Model: {vehicle_model}  \n"
                    f"• Vehicle Number: {vehicle_number}  \n"
                    f"• Parking Address: {parking_address}\n\n"
                    "Connecting you to a live agent now. In the meantime, here’s our Car Fumigation FAQ:"
                )
            )

            faq_text = (
                "Car Fumigation FAQ:\n\n"
                "1. What is car fumigation?\n"
                "   - A process that uses non-oily fog to eliminate pests in your vehicle.\n\n"
                "2. How long does it take?\n"
                "   - Usually 45–60 minutes, depending on vehicle size.\n\n"
                "3. Is it safe for upholstery?\n"
                "   - Yes, our chemicals are safe for fabrics and electronics.\n\n"
                "4. Do I need to remove personal items?\n"
                "   - We recommend removing loose items before fumigation.\n\n"
                "5. How soon can I drive after fumigation?\n"
                "   - You can drive immediately after the fog disperses (~5–10 min).\n\n"
                "If you have further questions, type 'reset' anytime or wait for our agent."
            )
            send_text_message(to=from_number, body=faq_text)
            return

        # F) any other text outside expected steps
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── 4) Fallback for any other payload types ───
    print(f"[DEBUG] handle_car_fumigation_flow: Unsupported msg_type='{msg_type}'")
    send_text_message(
        to=from_number,
        body="Sorry, I can’t handle that type of message. Type 'reset' to start over."
    )
    return
