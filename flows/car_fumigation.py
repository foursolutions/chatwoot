# flows/car_fumigation.py

import os
from datetime import datetime, timedelta
from flask import Response

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_list_message,
    send_text_message
)

# ────────────────────────────────────────────────────────────────────────────────
# 1) Main Menu (Template) — if the user needs to return to the very first screen.
# ────────────────────────────────────────────────────────────────────────────────
def send_main_menu(to: str, phone_number_id: str):
    """
    Calls the WhatsApp template 'main_menu_v2', with one placeholder ("there").
    """
    greeting_name = "there"
    resp = send_template_message(
        to=to,
        template_name="main_menu_v2",
        template_params=[greeting_name]
    )
    print(f"[DEBUG] send_main_menu → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 2) Pest Control Services → Now calls send_list_message (approved List Template)
# ────────────────────────────────────────────────────────────────────────────────
def send_pest_control_list(to: str, phone_number_id: str):
    """
    Instead of a free-form interactive payload, we invoke the /sendList helper.
    """
    # 'to' must be the full chatId: "6587788080@c.us"
    resp = send_list_message(to)
    print(f"[DEBUG] send_pest_control_list → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 3) Car Fumigation Menu → Template “car_fum_menu”
# ────────────────────────────────────────────────────────────────────────────────
def send_car_fum_menu(to: str, phone_number_id: str):
    resp = send_template_message(
        to=to,
        template_name="car_fum_menu",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_menu → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 4) Car Fumigation “Quote Options” (unused in most flows; kept for completeness)
# ────────────────────────────────────────────────────────────────────────────────
def send_car_fum_quote_options(to: str, phone_number_id: str):
    resp = send_template_message(
        to=to,
        template_name="car_fum_quote_options",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_quote_options → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 5) “Select Pest Type” → Interactive List (still free-form; two-level interaction is allowed)
# ────────────────────────────────────────────────────────────────────────────────
def send_pest_type_list(to: str, phone_number_id: str):
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Select Pest Type" },
            "body":   { "text": "Which pest are you seeing inside your vehicle?" },
            "footer": { "text": "Tap to choose" },
            "action": {
                "button": "Select Pest Type",
                "sections": [
                    {
                        "title": "Vehicle Pest Types",
                        "rows": [
                            { "id": "cockroach",  "title": "Cockroaches 🪳",  "description": "" },
                            { "id": "ants",       "title": "Ants 🐜",         "description": "" },
                            { "id": "lizards",    "title": "Lizards 🦎",      "description": "" },
                            { "id": "other_pest", "title": "Other Pest 🕷️",   "description": "" }
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_pest_type_list → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 6) “Select Vehicle Type” List
# ────────────────────────────────────────────────────────────────────────────────
def send_vehicle_type_list(to: str, phone_number_id: str):
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Select Vehicle Type" },
            "body":   { "text": "What type of vehicle do you drive?" },
            "footer": { "text": "Tap to choose" },
            "action": {
                "button": "Select Vehicle Type",
                "sections": [
                    {
                        "title": "Vehicle Types",
                        "rows": [
                            { "id": "vehicle_sedan",     "title": "Sedan/Hatchback",     "description": "Standard cars" },
                            { "id": "vehicle_suv",       "title": "SUV",                  "description": "Sport Utility Vehicle" },
                            { "id": "vehicle_mpv",       "title": "MPV",                  "description": "Multi-Purpose Vehicle" },
                            { "id": "vehicle_vans",      "title": "Vans/Lorries",         "description": "Commercial vehicles" },
                            { "id": "vehicle_ultra_luxury", "title": "Super/Luxury Cars", "description": "e.g. Bentley, Ferrari, etc." },
                            { "id": "vehicle_others",    "title": "Others",               "description": "Other vehicle types" }
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_vehicle_type_list → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 7) “Additional Care Fee” → Interactive Buttons (Yes / No)
# ────────────────────────────────────────────────────────────────────────────────
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
            "body": { "text": text },
            "action": {
                "buttons": [
                    { "type": "reply", "reply": { "id": "luxury_yes", "title": "Yes" } },
                    { "type": "reply", "reply": { "id": "luxury_no",  "title": "No"  } }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_cfadditionalfee_prompt → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 8) “Date Selection” → List of next 7 dates + “Other dates”
# ────────────────────────────────────────────────────────────────────────────────
def send_upcoming_dates_list(to: str, phone_number_id: str):
    today = datetime.now()
    base_day = today + timedelta(days=2)
    rows = []

    for i in range(7):
        date_obj = base_day + timedelta(days=i)
        date_str = date_obj.strftime("%d-%m-%Y")
        weekday  = date_obj.strftime("%A")
        title    = f"{date_str}, {weekday}"
        rows.append({
            "id": f"date_{date_str}",
            "title": title,
            "description": ""
        })

    # Add “Other dates” option
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
            "header": { "type": "text", "text": "Choose a Date" },
            "body":   { "text": "Please select one of the following dates:" },
            "footer": { "text": "Tap to choose" },
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
    print(f"[DEBUG] send_upcoming_dates_list → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 9) “Which Time?” → Interactive Buttons (Morning / Afternoon / Evening)
# ────────────────────────────────────────────────────────────────────────────────
def send_time_selection_prompt(to: str, phone_number_id: str, chosen_date: str):
    state = get_user_state("car", to) or {}
    state["appointment_date"] = chosen_date
    set_user_state("car", to, state)

    # Determine weekday name
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
            "body": { "text": text },
            "action": {
                "buttons": [
                    { "type": "reply", "reply": { "id": "time_morning",   "title": "Morning"   } },
                    { "type": "reply", "reply": { "id": "time_afternoon", "title": "Afternoon" } },
                    { "type": "reply", "reply": { "id": "time_evening",   "title": "Evening"   } }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_time_selection_prompt → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 10) “Quote Summary” → Interactive Buttons (Book Now / FAQ / Return to Main Menu)
# ────────────────────────────────────────────────────────────────────────────────
def send_quote_summary(to: str, phone_number_id: str):
    state = get_user_state("car", to) or {}

    if state.get("manual_quote", False):
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Below is the estimated breakdown of your quotation:\n\n"
            "- Car Model Type Pricing: Require agent to quote\n"
            "- Additional Care Fee: Require agent to quote\n"
            "- On-site Service Charge: Require agent to quote\n\n"
            "Estimated Total: Your vehicle requires agent quotation. "
            "Please allow our agent to assist you further.\n\n"
            "Please select an option below:"
        )
    else:
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
        set_user_state("car", to, state)

        additional_fee_str = f"${additional_fee}" if additional_fee != 0 else "$0"
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Here is your estimated breakdown:\n\n"
            f"- Car Model Pricing: ${base_quote}\n"
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
            "body": { "text": summary_text },
            "action": {
                "buttons": [
                    { "type": "reply", "reply": { "id": "book_appointment", "title": "Book Now" } },
                    { "type": "reply", "reply": { "id": "fumigation_faq",   "title": "More Info on Service" } },
                    { "type": "reply", "reply": { "id": "return_main_menu", "title": "Return to Main Menu" } }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_quote_summary → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 11) Car Fumigation FAQ → Interactive List of FAQs
# ────────────────────────────────────────────────────────────────────────────────
def send_car_fumigation_faq(to: str, phone_number_id: str):
    payload = {
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Car Fumigation FAQ" },
            "body":   { "text": "Select a FAQ question:" },
            "footer": { "text": "Tap an option" },
            "action": {
                "button": "Select FAQ",
                "sections": [
                    {
                        "title": "FAQ Questions",
                        "rows": [
                            {
                                "id": "cfq_safe",
                                "title": "Is it safe? Kids/Pets",
                                "description": "Safety with HACCP chemicals"
                            },
                            {
                                "id": "cfq_included",
                                "title": "Service Details",
                                "description": "What’s included in our service?"
                            },
                            {
                                "id": "cfq_warranty",
                                "title": "Our Warranty",
                                "description": "Warranty information"
                            },
                            {
                                "id": "cfq_preparation",
                                "title": "Preparation",
                                "description": "What to prepare before service"
                            },
                            {
                                "id": "cfq_duration",
                                "title": "Service Duration",
                                "description": "How long the service takes"
                            },
                            {
                                "id": "cfq_payment",
                                "title": "Payment Options",
                                "description": "Payment methods accepted"
                            }
                        ]
                    }
                ]
            }
        }
    }
    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_car_fumigation_faq → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 12) Process FAQ Response → Sends back the selected FAQ answer
# ────────────────────────────────────────────────────────────────────────────────
def process_car_fumigation_faq_response(to: str, faq_id: str):
    faq_answers = {
        "cfq_safe": (
            "Our car fumigation service ensures safety for your children and pets through:\n"
            "• NEA HACCP‐certified chemicals (safe even for F&B environments).\n"
            "• Non‐oily solutions, reducing residues.\n"
            "• Completely odorless treatment.\n"
            "• Professional fogging equipment, no aerosol residues."
        ),
        "cfq_included": (
            "Our car fumigation service includes:\n"
            "• Odorless, non‐oily HACCP‐grade chemical application.\n"
            "• Professional fogging machinery.\n"
            "• Complete interior disinfecting wipe‐down.\n"
            "• Vacuuming to remove all dead pests.\n"
            "• Application of a residual protective coating lasting up to 3 months."
        ),
        "cfq_warranty": (
            "We provide a 30-day warranty on all our car fumigation services.\n"
            "If pests return within this period, we will re-treat your vehicle at no extra cost."
        ),
        "cfq_preparation": (
            "Please remove all personal items from your vehicle, including:\n"
            "• Groceries\n"
            "• Toys\n"
            "• Electronics\n"
            "• Important documents\n\n"
            "Ensure that you ventilate the car for at least 10 minutes before service begins."
        ),
        "cfq_duration": (
            "Typical car fumigation takes 45–60 minutes.\n"
            "Please plan for an hour out of your day to accommodate the entire process."
        ),
        "cfq_payment": (
            "We accept:\n"
            "• Cash on site\n"
            "• Bank transfer (PayNow / PayLah!)\n"
            "• Credit/debit card (Visa, MasterCard)\n\n"
            "You can pay your technician directly after service."
        )
    }

    answer_text = faq_answers.get(faq_id, "Sorry, I couldn’t find that FAQ.")
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": answer_text }
    })


# ────────────────────────────────────────────────────────────────────────────────
# 13) handle_car_fumigation_flow: Routes through each step based on state["step"]
# ────────────────────────────────────────────────────────────────────────────────
def handle_car_fumigation_flow(to: str, message: dict, api_key: str, base_url: str):
    """
    to: the full chatId (e.g. '6587788080@c.us')
    message: the raw incoming JSON for this step
    """
    state = get_user_state("car", to) or {}
    msg_type = message.get("type", "")

    # ── Step 1: User tapped “Need help on Pest!” ──
    if msg_type == "button" and message.get("body", "").strip().lower() == "need help on pest!" and not state:
        state["step"] = "pest_control_list"
        set_user_state("car", to, state)

        # Instead of a free-form list, call the approved /sendList helper:
        send_pest_control_list(to, to)
        return Response(status=200)

    # ── Step 2: User picks “car_fumigation” from the Pest Control list ──
    if (
        msg_type == "interactive"
        and message.get("list_reply", {}).get("id") == "car_fumigation"
        and state.get("step") == "pest_control_list"
    ):
        state["step"] = "car_fum_menu"
        set_user_state("car", to, state)
        send_car_fum_menu(to, to)
        return Response(status=200)

    # ── Step 3: In car_fum_menu, user taps “Book Now” / “More Info on Service” / “Return to Main Menu” ──
    if msg_type == "button" and state.get("step") == "car_fum_menu":
        payload_text = message.get("body", "").strip().lower()

        if payload_text == "book appointment":
            state["step"] = "select_pest_type"
            set_user_state("car", to, state)
            send_pest_type_list(to, to)
            return Response(status=200)

        elif payload_text == "more info on service":
            state["step"] = "fumigation_faq"
            set_user_state("car", to, state)
            send_car_fumigation_faq(to, to)
            return Response(status=200)

        elif payload_text == "return to main menu":
            clear_user_state("car", to)
            send_main_menu(to, to)
            return Response(status=200)

    # ── Step 4: User taps a FAQ row ──
    if msg_type == "interactive" and state.get("step") == "fumigation_faq":
        faq_id = message.get("list_reply", {}).get("id")
        process_car_fumigation_faq_response(to, faq_id)
        return Response(status=200)

    # ── Step 5: User selected “Book Now” → Pest Type list ──
    if msg_type == "interactive" and state.get("step") == "select_pest_type":
        pest_choice = message.get("list_reply", {}).get("id")
        state["pest_type"] = pest_choice
        state["step"] = "select_vehicle_type"
        set_user_state("car", to, state)
        send_vehicle_type_list(to, to)
        return Response(status=200)

    # ── Step 6: User selected a vehicle type ──
    if msg_type == "interactive" and state.get("step") == "select_vehicle_type":
        vehicle_choice = message.get("list_reply", {}).get("id")
        state["vehicle"] = vehicle_choice

        if vehicle_choice in ["vehicle_ultra_luxury", "vehicle_others"]:
            state["manual_quote"] = True
            state["step"] = "quote_summary"
            set_user_state("car", to, state)
            send_quote_summary(to, to)
            return Response(status=200)

        state["manual_quote"] = False
        state["step"] = "ask_luxury_brand"
        set_user_state("car", to, state)
        send_cfadditionalfee_prompt(to, to)
        return Response(status=200)

    # ── Step 7: User answers “Yes” / “No” to Additional Care Fee ──
    if msg_type == "button" and state.get("step") == "ask_luxury_brand":
        payload_id = message.get("body", "").strip().lower()
        if payload_id == "yes":
            state["continental"] = "luxury_yes"
        else:
            state["continental"] = "luxury_no"
        state["step"] = "select_date"
        set_user_state("car", to, state)
        send_upcoming_dates_list(to, to)
        return Response(status=200)

    # ── Step 8: User tapped a date ──
    if msg_type == "interactive" and state.get("step") == "select_date":
        date_id = message.get("list_reply", {}).get("id")

        if date_id == "other_dates":
            state["step"] = "await_manual_date"
            set_user_state("car", to, state)
            send_text_message({
                "to": to,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "Please type your preferred appointment date in DD-MM-YYYY format." }
            })
            return Response(status=200)
        else:
            chosen_date = date_id.split("_", 1)[1]
            state["step"] = "select_time"
            set_user_state("car", to, state)
            send_time_selection_prompt(to, to, chosen_date)
            return Response(status=200)

    # ── Step 9: User typed a date manually ──
    if msg_type == "text" and state.get("step") == "await_manual_date":
        user_date = message["text"]["body"].strip()
        try:
            datetime.strptime(user_date, "%d-%m-%Y")
            state["step"] = "select_time"
            set_user_state("car", to, state)
            send_time_selection_prompt(to, to, user_date)
        except Exception:
            send_text_message({
                "to": to,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {
                    "body": "I couldn't parse that. Please type date as DD-MM-YYYY (e.g. 12-06-2025)."
                }
            })
        return Response(status=200)

    # ── Step 10: User tapped “Morning” / “Afternoon” / “Evening” ──
    if msg_type == "button" and state.get("step") == "select_time":
        payload_id = message.get("body", "").strip().lower()
        if payload_id == "time morning":
            chosen_time = "10:00 - 12:00"
        elif payload_id == "time afternoon":
            chosen_time = "12:00 - 18:00"
        elif payload_id == "time evening":
            chosen_time = "18:00 - 23:59"
        else:
            chosen_time = ""

        state["appointment_time"] = chosen_time
        state["step"] = "collect_final_details"
        set_user_state("car", to, state)

        send_text_message({
            "to": to,
            "type": "text",
            "messaging_product": "whatsapp",
            "text": {
                "body": (
                    "Great! Please reply in one sentence using **this format, separated by commas**:\n\n"
                    "Vehicle Model, Vehicle Number, On-site Location\n"
                    "For example:\n"
                    "**Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559**"
                )
            }
        })
        return Response(status=200)

    # ── Step 11: User sends final details text ──
    if msg_type == "text" and state.get("step") == "collect_final_details":
        parts = [p.strip() for p in message["text"]["body"].split(",")]
        if len(parts) != 3:
            send_text_message({
                "to": to,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {
                    "body": (
                        "Sorry, I couldn’t parse that.\n\n"
                        "Please reply in one sentence using **this format, separated by commas**:\n\n"
                        "Vehicle Model, Vehicle Number, On-site Location\n"
                        "For example:\n"
                        "**Toyota Wish, SSS4444X, Tampines North Drive 1, Singapore 528559**"
                    )
                }
            })
            return Response(status=200)

        vehicle_model   = parts[0]
        vehicle_number  = parts[1]
        parking_address = parts[2]

        state["vehicle_model"]   = vehicle_model
        state["vehicle_number"]  = vehicle_number
        state["parking_address"] = parking_address

        pest_encountered = state.get("pest_type", "N/A")
        total_quote      = state.get("computed_quote", "N/A")
        appointment_date = state.get("appointment_date", "")
        appointment_time = state.get("appointment_time", "")

        clear_user_state("car", to)

        confirmation_text = (
            "Thank you! Your appointment request has been received.\n\n"
            "Details provided:\n\n"
            f"• Pest Encountered: {pest_encountered}\n"
            f"• Estimated Quote: ${total_quote}\n"
            f"• Date: {appointment_date}\n"
            f"• Time: {appointment_time}\n"
            f"• Vehicle Model: {vehicle_model}\n"
            f"• Vehicle Number: {vehicle_number}\n"
            f"• Parking Address: {parking_address}\n\n"
            "We’re connecting you to a live agent now. Meanwhile, you may review our Car Fumigation FAQ:"
        )
        send_text_message({
            "to": to,
            "type": "text",
            "messaging_product": "whatsapp",
            "text": { "body": confirmation_text }
        })

        send_car_fumigation_faq(to, to)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────────
    # Fallback (if no step matched): clear state & send main menu
    # ─────────────────────────────────────────────────────────────────────────────
    clear_user_state("car", to)
    send_main_menu(to, to)
    return Response(status=200)
