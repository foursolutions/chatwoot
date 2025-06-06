# flows/car_fumigation.py

import os
import time
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
    # The template name “main_menu_v2” is read from the environment variable MAIN_MENU_TEMPLATE.
    template_name = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2")
    resp = send_template_message(
        to=plain_phone,
        template_name=template_name,
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
    resp = send_list_message(
        to=chat_id.split("@")[0],
        # Our helper send_list_message() expects its first argument to be the phone number
        # without “@c.us”. Internally, it appends “@c.us” again when constructing the JSON.
    )
    print(f"[DEBUG] send_pest_control_list → {resp}")
    return resp


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
def send_vehicle_type_list(to: str) -> dict:
    """
    to: plain phone number (e.g. "6587788080")
    Sends a free-form interactive list of vehicle types via 1msg’s /sendList format.
    """
    chat_id = f"{to}@c.us"
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
                            { "id": "vehicle_sedan",          "title": "Sedan/Hatchback",     "description": "Standard cars"       },
                            { "id": "vehicle_suv",            "title": "SUV",                 "description": "Sport Utility Vehicle" },
                            { "id": "vehicle_mpv",            "title": "MPV",                 "description": "Multi-Purpose Vehicle" },
                            { "id": "vehicle_vans",           "title": "Vans/Lorries",        "description": "Commercial vehicles"  },
                            { "id": "vehicle_ultra_luxury",   "title": "Super/Luxury Cars",   "description": "e.g. Bentley, Ferrari, etc." },
                            { "id": "vehicle_others",         "title": "Others",              "description": "Other vehicle types" }
                        ]
                    }
                ]
            }
        }
    }

    resp = send_list_message(**payload)
    print(f"[DEBUG] send_vehicle_type_list → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# 5) send_additional_fee_prompt: Ask “Do you drive any of these brands? Yes/No”
# ────────────────────────────────────────────────────────────────────────────────
def send_additional_fee_prompt(to: str) -> dict:
    """
    to: plain phone number (e.g. "6587788080")
    That quick yes/no (buttons) about “Additional care fee?”
    """
    chat_id = f"{to}@c.us"
    text = (
        "Does your vehicle belong to any of these brands?\n\n"
        "• Mercedes-Benz\n"
        "• BMW\n"
        "• Audi\n"
        "• Lexus\n"
        "• Porsche\n"
        "• Jaguar\n"
        "• Tesla\n"
        "• Range Rover\n\n"
        "Please reply Yes or No."
    )

    resp = send_text_message({
        "to":   to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": text }
    })
    print(f"[DEBUG] send_additional_fee_prompt(text) → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# 6) send_quote_summary: final quotation summary with “Book Now / FAQ / Return”
# ────────────────────────────────────────────────────────────────────────────────
def send_quote_summary(chat_id: str) -> Response:
    """
    Summarizes all of the data collected so far, then prompts:
      “Book Now / FAQ / Return to main menu” as text/buttons.
    chat_id: full WhatsApp ID, e.g. "6587788080@c.us"
    """
    state = get_user_state("car", chat_id) or {}
    manual_quote = state.get("manual_quote", False)

    if manual_quote:
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Below is the estimated breakdown of your quotation:\n\n"
            "- Car Model Type Pricing: Agent quote needed\n"
            "- Additional Care Fee: Agent quote needed\n"
            "- On-site Service Charge: Agent quote needed\n\n"
            "Estimated Total: Pending agent quote. Our agent will assist you shortly.\n\n"
            "Please select an option below:\n"
            "• Book Now\n"
            "• FAQ\n"
            "• Return to Main Menu"
        )

        send_text_message({
            "to": chat_id.split("@")[0],
            "type": "text",
            "messaging_product": "whatsapp",
            "text": { "body": summary_text }
        })

        time.sleep(1)

        # After the summary, send a quick FAQ list (via send_list_message):
        faq_sections = [
            {
                "title": "Car Fumigation FAQ",
                "rows": [
                    { "id": "cfum_faq_safe",      "title": "Is it safe?",          "description": "Is fumigation safe for kids/pets?" },
                    { "id": "cfum_faq_included",  "title": "Service Details",      "description": "What's included?" },
                    { "id": "cfum_faq_warranty",  "title": "Warranty",             "description": "Coverage & terms" },
                    { "id": "cfum_faq_duration",  "title": "Duration",             "description": "How long does it take?" }
                ]
            }
        ]

        send_list_message(
            to=chat_id.split("@")[0],
            body="Select a Car-Fumigation FAQ question:",
            header="Car Fumigation FAQ",
            footer="Tap to choose",
            action_button="Select FAQ",
            sections=faq_sections
        )

        return Response(status=200)

    # If not manual_quote (i.e. all fields known), build a calculated quote:
    # (Example calculation—replace with your real logic.)
    pest_type     = state.get("pest_type", "Unknown")
    vehicle_type  = state.get("vehicle_type", "Unknown")
    base_price    = {"vehicle_sedan": 80, "vehicle_suv": 100, "vehicle_mpv": 120}.get(vehicle_type, 150)
    additional_fee = 20 if state.get("additional_fee") == "yes" else 0
    total_price   = base_price + additional_fee + 30  # + $30 fixed on-site charge

    summary_text = (
        f"On-Site Car Fumigation Quotation\n\n"
        f"- Pest Type: {pest_type}\n"
        f"- Vehicle Type: {vehicle_type}\n"
        f"- Base Price: ${base_price}\n"
    )
    if additional_fee:
        summary_text += f"- Additional Care Fee: ${additional_fee}\n"
    summary_text += "- On-site Service Charge: $30\n\n"
    summary_text += f"Estimated Total: ${total_price}\n\n"
    summary_text += "Please select an option below:\n"
    summary_text += "• Book Now\n"
    summary_text += "• FAQ\n"
    summary_text += "• Return to Main Menu"

    send_text_message({
        "to": chat_id.split("@")[0],
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": summary_text }
    })

    time.sleep(1)

    # Show the same FAQ list after the summary:
    faq_sections = [
        {
            "title": "Car Fumigation FAQ",
            "rows": [
                { "id": "cfum_faq_safe",      "title": "Is it safe?",          "description": "Is fumigation safe for kids/pets?" },
                { "id": "cfum_faq_included",  "title": "Service Details",      "description": "What's included?" },
                { "id": "cfum_faq_warranty",  "title": "Warranty",             "description": "Coverage & terms" },
                { "id": "cfum_faq_duration",  "title": "Duration",             "description": "How long does it take?" }
            ]
        }
    ]

    send_list_message(
        to=chat_id.split("@")[0],
        body="Select a Car-Fumigation FAQ question:",
        header="Car Fumigation FAQ",
        footer="Tap to choose",
        action_button="Select FAQ",
        sections=faq_sections
    )

    return Response(status=200)


# ────────────────────────────────────────────────────────────────────────────────
# 7) process_car_fumigation_faq_response: When user taps a “cfum_faq_*” row
# ────────────────────────────────────────────────────────────────────────────────
def process_car_fumigation_faq_response(to: str, faq_id: str) -> None:
    """
    After the user taps one of the FAQ rows (id starts with "cfum_faq_"), send
    the corresponding answer, then re-show the FAQ list.
    """
    faq_answers = {
        "cfum_faq_safe": (
            "Yes—our car-fumigation treatments are eco-friendly and safe for you, "
            "your family, and your pets.\n\n"
            "We only use NEA-approved chemicals and minimal odors. Expect to drive "
            "your vehicle again in <1 hour after service."
        ),
        "cfum_faq_included": (
            "Our car-fumigation package includes:\n"
            "• Inspection of your vehicle’s cabin & engine bay\n"
            "• Professional fumigation & fogging of entire car interior\n"
            "• Disinfectant application to seats, carpets, mats\n"
            "• Complimentary post-service inspection within 7 days"
        ),
        "cfum_faq_warranty": (
            "We offer a 30-day warranty on all car-fumigation services.\n\n"
            "If pests reappear within 30 days, simply let us know and we’ll re-treat at no extra cost."
        ),
        "cfum_faq_duration": (
            "Most sedans take about 20–30 minutes to fumigate. Larger SUVs/MPVs may "
            "take 30–45 minutes depending on size and condition."
        )
    }
    answer = faq_answers.get(faq_id, "Sorry, no info is available for that question.")
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": answer }
    })


# ────────────────────────────────────────────────────────────────────────────────
# 8) handle_car_fumigation_flow: Full flow handler
# ────────────────────────────────────────────────────────────────────────────────
def handle_car_fumigation_flow(
    to_chat_id: str,
    message: dict,
    user_state: dict,
    api_key: str,
    base_url: str
) -> Response:
    """
    Drives the Car-Fumigation flow based on user_state["step"].

    to_chat_id:   e.g. "6591234567@c.us"
    user_state:   an in-memory dict stored by get_user_state("car", phone_no)
    message:      the incoming message dict from 1msg
    """

    state = user_state or {}
    step  = state.get("step", "")
    msg_type = message.get("type")  # "chat", "button", or "interactive"

    # Helper to extract “button” payload from a button-reply:
    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"].get("payload", "")
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"].get("id", "")
        return ""

    # ─── A) If msg_type=="interactive" & user was in a “list” step, handle list_replies
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_car_fumigation_flow: LIST payload='{choice_id}'")

        # Step: "select_pest_type" → they chose which pest service
        if step == "select_pest_type":
            state["pest_type"] = choice_id
            set_user_state("car", to_chat_id, state)

            # Next → “select_vehicle_type”
            state["step"] = "select_vehicle_type"
            set_user_state("car", to_chat_id, state)
            send_vehicle_type_list(to_chat_id.split("@")[0])
            return Response(status=200)

        # Step: "select_vehicle_type" → they chose vehicle type
        if step == "select_vehicle_type":
            vehicle_choice = message["interactive"]["list_reply"]["id"]
            state["vehicle_type"] = vehicle_choice
            set_user_state("car", to_chat_id, state)

            # Determine if this brand requires manual quote:
            if vehicle_choice in ["vehicle_ultra_luxury", "vehicle_others"]:
                state["manual_quote"] = True
                state["step"] = "quote_summary"
                set_user_state("car", to_chat_id, state)
                return send_quote_summary(to_chat_id)

            # Otherwise, no manual quote needed; go to “additional_fee” step
            state["manual_quote"] = False
            state["step"] = "additional_fee"
            set_user_state("car", to_chat_id, state)
            return send_additional_fee_prompt(to_chat_id.split("@")[0])

    # ─── B) If msg_type=="button" or an interactive “button_reply”
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message).lower()
        print(f"[DEBUG] handle_car_fumigation_flow: BUTTON payload='{payload}'")

        # Step 1: User tapped “need_help_on_pest!” (main menu button)
        if payload == "need help on pest!":
            clear_user_state("car", to_chat_id)
            new_state = { "step": "select_pest_type" }
            set_user_state("car", to_chat_id, new_state)
            send_pest_control_list(to_chat_id.split("@")[0])
            return Response(status=200)

        # Step 2: After they pick a pest (e.g., “help_pest”)
        if step == "select_pest_type":
            # Unlikely to hit here because we handle the list-reply above.
            send_text_message({
                "to": to_chat_id.split("@")[0],
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "Please use the list to pick a pest type." }
            })
            return Response(status=200)

        # Step 3: After “select_vehicle_type” (handled above in A)
        # We fall through to here only if they typed something else.
        if step == "additional_fee":
            # Expecting "yes" or "no" text (since we asked them to reply Yes/No).
            text = message.get("body", "").strip().lower()
            if text in ["yes", "y"]:
                state["additional_fee"] = "yes"
                state["step"] = "quote_summary"
                set_user_state("car", to_chat_id, state)
                return send_quote_summary(to_chat_id)
            elif text in ["no", "n"]:
                state["additional_fee"] = "no"
                state["step"] = "quote_summary"
                set_user_state("car", to_chat_id, state)
                return send_quote_summary(to_chat_id)
            else:
                send_text_message({
                    "to": to_chat_id.split("@")[0],
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "Please reply Yes or No." }
                })
                return Response(status=200)

        # Step 4: Final step—User types “Book Now,” “FAQ,” or “Return to Main Menu”
        if step == "quote_summary":
            text = message.get("body", "").strip().lower()
            if text == "book now":
                send_text_message({
                    "to": to_chat_id.split("@")[0],
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "✅ Thank you! Your booking is confirmed. Our technician will be in touch soon." }
                })
                clear_user_state("car", to_chat_id)
                return Response(status=200)

            if text == "faq":
                # Re-show the FAQ list (just like process_car_fumigation_faq_response does)
                faq_sections = [
                    {
                        "title": "Car Fumigation FAQ",
                        "rows": [
                            { "id": "cfum_faq_safe",      "title": "Is it safe?",          "description": "Is fumigation safe?" },
                            { "id": "cfum_faq_included",  "title": "Service Details",      "description": "What's included?" },
                            { "id": "cfum_faq_warranty",  "title": "Warranty",             "description": "Coverage & terms" },
                            { "id": "cfum_faq_duration",  "title": "Duration",             "description": "How long does it take?" }
                        ]
                    }
                ]
                send_list_message(
                    to=to_chat_id.split("@")[0],
                    body="Select a Car-Fumigation FAQ question:",
                    header="Car Fumigation FAQ",
                    footer="Tap to choose",
                    action_button="Select FAQ",
                    sections=faq_sections
                )
                return Response(status=200)

            if text == "return to main menu":
                clear_user_state("car", to_chat_id)
                # Re-show the top-level main menu (template) via helper:
                send_template_message(
                    to=to_chat_id.split("@")[0],
                    template_name=os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2"),
                    template_params=["there"]
                )
                return Response(status=200)

            # Fallback if they typed anything else:
            send_text_message({
                "to": to_chat_id.split("@")[0],
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "Sorry, I didn’t understand that. Type 'reset' to start over." }
            })
            return Response(status=200)

    # ─── C) If we fell through (no valid list/button matched), clear state & send main menu
    clear_user_state("car", to_chat_id)
    send_main_menu(to_chat_id.split("@")[0])
    return Response(status=200)
