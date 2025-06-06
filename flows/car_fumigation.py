# flows/car_fumigation.py

import os
from datetime import datetime, timedelta
from flask import Response

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_template_message,
    send_list_message
)


# ────────────────────────────────────────────────────────────────────────────────
# 1) send_main_menu: send the “main_menu_v2” template (greeting = "there")
# ────────────────────────────────────────────────────────────────────────────────
def send_main_menu(plain_phone: str):
    """
    plain_phone: e.g. "6587788080"
    Calls pre-approved template "main_menu_v2" with placeholder "there".
    """
    resp = send_template_message(
        to=plain_phone,
        template_name="main_menu_v2",
        template_params=["there"]
    )
    print(f"[DEBUG] send_main_menu → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 2) send_pest_control_list: Use 1msg’s /sendList endpoint
# ────────────────────────────────────────────────────────────────────────────────
def send_pest_control_list(chat_id: str):
    """
    chat_id: full WhatsApp ID, e.g. "6587788080@c.us".
    Uses send_list_message(...) so WhatsApp will reliably render it as a List.
    """
    resp = send_list_message(chat_id)
    print(f"[DEBUG] send_pest_control_list → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 3) send_car_fum_menu: Show “car_fum_menu” template to pick Book/FAQ/Return
# ────────────────────────────────────────────────────────────────────────────────
def send_car_fum_menu(chat_id: str):
    """
    chat_id: full WhatsApp ID, e.g. "6587788080@c.us"
    For templates, strip “@c.us” and call send_template_message.
    """
    plain_phone = chat_id.split("@")[0]
    resp = send_template_message(
        to=plain_phone,
        template_name="car_fum_menu",
        template_params=[]
    )
    print(f"[DEBUG] send_car_fum_menu → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 4) send_vehicle_type_list: “Select Vehicle Type” interactive list
# ────────────────────────────────────────────────────────────────────────────────
def send_vehicle_type_list(chat_id: str):
    """
    chat_id: full WhatsApp ID, e.g. "6587788080@c.us".
    Sends a free-form interactive list of vehicle types via 1msg’s /send endpoint.
    """
    payload = {
        "to": chat_id,
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
                            {
                                "id": "vehicle_sedan",
                                "title": "Sedan/Hatchback",
                                "description": "Standard cars"
                            },
                            {
                                "id": "vehicle_suv",
                                "title": "SUV",
                                "description": "Sport Utility Vehicle"
                            },
                            {
                                "id": "vehicle_mpv",
                                "title": "MPV",
                                "description": "Multi-Purpose Vehicle"
                            },
                            {
                                "id": "vehicle_vans",
                                "title": "Vans/Lorries",
                                "description": "Commercial vehicles"
                            },
                            {
                                "id": "vehicle_ultra_luxury",
                                "title": "Super/Luxury Cars",
                                "description": "e.g. Bentley, Ferrari, etc."
                            },
                            {
                                "id": "vehicle_others",
                                "title": "Others",
                                "description": "Other vehicle types"
                            }
                        ]
                    }
                ]
            }
        }
    }
    # Because this is a free-form list (not a pre-approved template), watch for
    # 1msg’s response “saving history disabled” in your logs.
    resp = send_text_message({
        "to": chat_id.split("@")[0],
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": payload["interactive"]
    })
    print(f"[DEBUG] send_vehicle_type_list → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 5) send_cfadditionalfee_prompt: “Additional Care Fee” (Yes/No buttons)
# ────────────────────────────────────────────────────────────────────────────────
def send_cfadditionalfee_prompt(chat_id: str):
    text = (
        "Does your vehicle belong to any of these brands?\n\n"
        "Mercedes-Benz\nBMW\nAudi\nLexus\nPorsche\nJaguar\nTesla\nRange Rover\n\n"
        "These brands require special care during servicing.\n"
        "Please reply Yes or No."
    )
    # We’ll send a “button”‐style interactive via 1msg’s /send endpoint:
    resp = send_text_message({
        "to": chat_id.split("@")[0],
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
    })
    print(f"[DEBUG] send_cfadditionalfee_prompt → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 6) send_upcoming_dates_list: “Choose a Date” (next 7 days + “Other dates”)
# ────────────────────────────────────────────────────────────────────────────────
def send_upcoming_dates_list(chat_id: str):
    today = datetime.now()
    base_day = today + timedelta(days=2)
    rows = []

    for i in range(7):
        date_obj = base_day + timedelta(days=i)
        date_str = date_obj.strftime("%d-%m-%Y")
        weekday  = date_obj.strftime("%A")
        rows.append({
            "id": f"date_{date_str}",
            "title": f"{date_str}, {weekday}",
            "description": ""
        })

    rows.append({
        "id": "other_dates",
        "title": "Other dates",
        "description": "Select a different date using DD-MM-YYYY"
    })

    resp = send_text_message({
        "to": chat_id.split("@")[0],
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
    })
    print(f"[DEBUG] send_upcoming_dates_list → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 7) send_time_selection_prompt: “Which Time?” (Morning/Afternoon/Evening buttons)
# ────────────────────────────────────────────────────────────────────────────────
def send_time_selection_prompt(chat_id: str, chosen_date: str):
    state = get_user_state("car", chat_id) or {}
    state["appointment_date"] = chosen_date
    set_user_state("car", chat_id, state)

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
    resp = send_text_message({
        "to": chat_id.split("@")[0],
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
    })
    print(f"[DEBUG] send_time_selection_prompt → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 8) send_quote_summary: final quotation summary with “Book Now / FAQ / Return”
# ────────────────────────────────────────────────────────────────────────────────
def send_quote_summary(chat_id: str):
    state = get_user_state("car", chat_id) or {}

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
        set_user_state("car", chat_id, state)

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

    resp = send_text_message({
        "to": chat_id.split("@")[0],
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "button",
            "body": { "text": summary_text },
            "action": {
                "buttons": [
                    { "type": "reply", "reply": { "id": "book_appointment", "title": "Book Now"             } },
                    { "type": "reply", "reply": { "id": "fumigation_faq",   "title": "More Info on Service" } },
                    { "type": "reply", "reply": { "id": "return_main_menu", "title": "Return to Main Menu"} }
                ]
            }
        }
    })
    print(f"[DEBUG] send_quote_summary → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 9) send_car_fumigation_faq: show “Car Fumigation FAQ” as an interactive list
# ────────────────────────────────────────────────────────────────────────────────
def send_car_fumigation_faq(chat_id: str):
    payload = {
        "to": chat_id,
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
    resp = send_text_message({
        "to": chat_id.split("@")[0],
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": payload["interactive"]
    })
    print(f"[DEBUG] send_car_fumigation_faq → {resp}")


# ────────────────────────────────────────────────────────────────────────────────
# 10) process_car_fumigation_faq_response: send back the selected FAQ answer
# ────────────────────────────────────────────────────────────────────────────────
def process_car_fumigation_faq_response(chat_id: str, faq_id: str):
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
        "to": chat_id.split("@")[0],  # plain digits
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": answer_text }
    })


# ────────────────────────────────────────────────────────────────────────────────
# 11) handle_car_fumigation_flow: Main dispatcher for each step in “car” flow
# ────────────────────────────────────────────────────────────────────────────────
def handle_car_fumigation_flow(to_chat_id: str, message: dict, api_key: str, base_url: str):
    """
    to_chat_id: full WhatsApp ID, e.g. "6587788080@c.us"
    message: raw incoming JSON
    """
    state = get_user_state("car", to_chat_id) or {}
    msg_type = message.get("type", "")

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 1: User tapped “Need help on Pest!” (button)
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "button"
        and message.get("body", "").strip().lower() == "need help on pest!"
        and not state):
        state["step"] = "pest_control_list"
        set_user_state("car", to_chat_id, state)

        send_pest_control_list(to_chat_id)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 2: User selected “car_fumigation” from the Pest Control list
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "interactive"
        and message.get("list_reply", {}).get("id") == "car_fumigation"
        and state.get("step") == "pest_control_list"):
        state["step"] = "car_fum_menu"
        set_user_state("car", to_chat_id, state)

        send_car_fum_menu(to_chat_id)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 3: In car_fum_menu, user taps “Book Now” / “More Info on Service” / “Return to Main Menu”
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "button"
        and state.get("step") == "car_fum_menu"):
        payload_text = message.get("body", "").strip().lower()

        if payload_text == "book appointment":
            state["step"] = "select_pest_type"
            set_user_state("car", to_chat_id, state)

            # Show Pest Control list again for “which pest”
            send_pest_control_list(to_chat_id)
            return Response(status=200)

        elif payload_text == "more info on service":
            state["step"] = "fumigation_faq"
            set_user_state("car", to_chat_id, state)

            send_car_fumigation_faq(to_chat_id)
            return Response(status=200)

        elif payload_text == "return to main menu":
            clear_user_state("car", to_chat_id)
            send_main_menu(to_chat_id.split("@")[0])
            return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 4: User selected a FAQ row (in the “fumigation_faq” step)
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "interactive"
        and state.get("step") == "fumigation_faq"):
        faq_id = message.get("list_reply", {}).get("id")
        process_car_fumigation_faq_response(to_chat_id, faq_id)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 5: User selected “Book Now” → now selecting pest type again
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "interactive"
        and state.get("step") == "select_pest_type"):
        pest_choice = message.get("list_reply", {}).get("id")
        state["pest_type"] = pest_choice

        # Move to vehicle‐type step
        state["step"] = "select_vehicle_type"
        set_user_state("car", to_chat_id, state)

        # *** FIXED: call the newly defined send_vehicle_type_list(...) ***
        send_vehicle_type_list(to_chat_id)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 6: User selected a vehicle type from the “Select Vehicle Type” list
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "interactive"
        and state.get("step") == "select_vehicle_type"):
        vehicle_choice = message.get("list_reply", {}).get("id")
        state["vehicle"] = vehicle_choice

        # If “Super/Luxury Cars” or “Others”, skip straight to manual quote
        if vehicle_choice in ["vehicle_ultra_luxury", "vehicle_others"]:
            state["manual_quote"] = True
            state["step"] = "quote_summary"
            set_user_state("car", to_chat_id, state)

            send_quote_summary(to_chat_id)
            return Response(status=200)

        # Otherwise, ask about Additional Care Fee
        state["manual_quote"] = False
        state["step"] = "ask_luxury_brand"
        set_user_state("car", to_chat_id, state)

        send_cfadditionalfee_prompt(to_chat_id)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 7: User answered “Yes” / “No” to “Additional Care Fee” (buttons)
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "button"
        and state.get("step") == "ask_luxury_brand"):
        payload_id = message.get("body", "").strip().lower()
        if payload_id == "yes":
            state["continental"] = "luxury_yes"
        else:
            state["continental"] = "luxury_no"
        state["step"] = "select_date"
        set_user_state("car", to_chat_id, state)

        send_upcoming_dates_list(to_chat_id)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 8: User selected a date from the “Upcoming Dates” list
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "interactive"
        and state.get("step") == "select_date"):
        date_id = message.get("list_reply", {}).get("id")

        if date_id == "other_dates":
            state["step"] = "await_manual_date"
            set_user_state("car", to_chat_id, state)

            send_text_message({
                "to": to_chat_id.split("@")[0],
                "type": "text",
                "text": {
                    "body": "Please type your preferred appointment date in DD-MM-YYYY format."
                }
            })
            return Response(status=200)
        else:
            chosen_date = date_id.split("_", 1)[1]
            state["step"] = "select_time"
            set_user_state("car", to_chat_id, state)

            send_time_selection_prompt(to_chat_id, chosen_date)
            return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 9: User manually typed a date (step="await_manual_date")
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "text"
        and state.get("step") == "await_manual_date"):
        user_date = message["body"].strip()
        try:
            datetime.strptime(user_date, "%d-%m-%Y")
            state["step"] = "select_time"
            set_user_state("car", to_chat_id, state)

            send_time_selection_prompt(to_chat_id, user_date)
        except Exception:
            send_text_message({
                "to": to_chat_id.split("@")[0],
                "type": "text",
                "text": {
                    "body": "I couldn't parse that. Please type date as DD-MM-YYYY (e.g. 12-06-2025)."
                }
            })
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 10: User tapped a “Morning/Afternoon/Evening” button (step="select_time")
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "button"
        and state.get("step") == "select_time"):
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
        set_user_state("car", to_chat_id, state)

        send_text_message({
            "to": to_chat_id.split("@")[0],
            "type": "text",
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

    # ─────────────────────────────────────────────────────────────────────────██
    # Step 11: User replies “Vehicle Model, Vehicle Number, On-site Location”
    # ─────────────────────────────────────────────────────────────────────────██
    if (msg_type == "text"
        and state.get("step") == "collect_final_details"):
        parts = [p.strip() for p in message["body"].split(",")]
        if len(parts) != 3:
            send_text_message({
                "to": to_chat_id.split("@")[0],
                "type": "text",
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

        # Clear the “car” flow entirely (we’re done)
        clear_user_state("car", to_chat_id)

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
            "to": to_chat_id.split("@")[0],
            "type": "text",
            "text": { "body": confirmation_text }
        })

        send_car_fumigation_faq(to_chat_id)
        return Response(status=200)

    # ─────────────────────────────────────────────────────────────────────────██
    # Fallback: no step matched → clear state & send main menu again
    # ─────────────────────────────────────────────────────────────────────────██
    clear_user_state("car", to_chat_id)
    send_main_menu(to_chat_id.split("@")[0])
    return Response(status=200)
