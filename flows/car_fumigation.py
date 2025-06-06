# flows/car_fumigation.py

import os
import time
from flask import Response

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_list_message
)


# ────────────────────────────────────────────────────────────────────────────────
# 1) send_main_menu: Show the three-button menu: Pest / Mold / Live Human
# ────────────────────────────────────────────────────────────────────────────────
def send_main_menu(to: str) -> dict:
    """
    This function is called when we want to display the top-level menu:
      • Need help on Pest!
      • Need help on Mold!
      • Live Human
    We now do this via a Template, but can also keep a backup button-style version.
    """

    # We’re using send_template_message(...) in dispatcher.  But if you wanted
    # to send an interactive button version instead, you could create a fallback.

    # For completeness, we return an empty dict (since dispatcher prints the template response).
    # If you ever want to send a button instead, you can implement send_interactive here.

    return {}  # just a placeholder, since your dispatcher already does send_template


# ────────────────────────────────────────────────────────────────────────────────
# 2) send_pest_control_list: Show the list of pest types (“Urban Pest”, “Rodent”, etc.)
# ────────────────────────────────────────────────────────────────────────────────
def send_pest_control_list(to: str) -> dict:
    """
    This function sends a WhatsApp interactive list of pest-control categories:
      • Urban Pest
      • Rodent
      • Termite
    etc. Follow 1msg’s /sendList format.
    """
    header = "Pest Control Services"
    body = "Please select the pest control service you need assistance with:\n"
    footer = "Tap to choose"
    action_button = "Select Service"

    sections = [
        {
            "title": "Common Pest Issues",
            "rows": [
                {
                    "id": "help_pest",
                    "title": "Urban Pest",
                    "description": "Roaches, ants, mosquitoes, etc."
                },
                {
                    "id": "help_rodent",
                    "title": "Rodent Control",
                    "description": "Rats, mice, etc."
                },
                {
                    "id": "help_termite",
                    "title": "Termite Control",
                    "description": "Termite inspection & treatment"
                }
            ]
        }
    ]

    resp = send_list_message(
        to=to,
        body=body,
        header=header,
        footer=footer,
        action_button=action_button,
        sections=sections
    )
    print(f"[DEBUG] send_pest_control_list → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# 3) send_vehicle_type_list: When user picks e.g. “help_pest”, we show vehicle type
# ────────────────────────────────────────────────────────────────────────────────
def send_vehicle_type_list(to: str) -> dict:
    """
    After they pick “help_pest” (car fumigation), we ask “What type of vehicle?”
    This is a list of cars/SUVs/mpv/etc.
    """
    header = "Select Vehicle Type"
    body = "What type of vehicle do you drive?"
    footer = "Tap to choose"
    action_button = "Select Vehicle Type"

    sections = [
        {
            "title": "Vehicle Types",
            "rows": [
                { "id": "vehicle_sedan",       "title": "Sedan/Hatchback",      "description": "Standard cars"            },
                { "id": "vehicle_suv",         "title": "SUV",                  "description": "Sport Utility Vehicle"    },
                { "id": "vehicle_mpvl",        "title": "MPV",                  "description": "Multi-Purpose Vehicle"    },
                { "id": "vehicle_vans",        "title": "Vans / Lorries",       "description": "Commercial vehicles"      },
                { "id": "vehicle_ultra_luxury", "title": "Super / Luxury Cars",   "description": "e.g. Bentley, Ferrari, etc." },
                { "id": "vehicle_others",      "title": "Others",               "description": "Other vehicle types"      }
            ]
        }
    ]

    resp = send_list_message(
        to=to,
        body=body,
        header=header,
        footer=footer,
        action_button=action_button,
        sections=sections
    )
    print(f"[DEBUG] send_vehicle_type_list → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# 4) send_additional_fee_prompt: Ask “Do you drive any of these brands? Yes/No”
# ────────────────────────────────────────────────────────────────────────────────
def send_additional_fee_prompt(to: str) -> dict:
    """
    That quick yes/no (buttons) about “Additional care fee?”
    """
    # For a simple yes/no, we can fall back to plain text (asking them to type "Yes"/"No"),
    # or implement a quick two-button interactive payload.  Here’s a minimal button version:
    from helpers import send_text_message

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
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": text}
    })
    print(f"[DEBUG] send_additional_fee_prompt(text) → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# 5) send_quote_summary: final quotation summary with “Book Now / FAQ / Return”
# ────────────────────────────────────────────────────────────────────────────────
def send_quote_summary(chat_id: str) -> Response:
    """
    Summarizes all of the data collected so far, then prompts: “Book Now / More Info / Return to main menu” as buttons.
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
            "Estimated Total: Pending agent quote.  Our agent will assist you shortly.\n\n"
            "Please select an option below:\n"
            "• Book Now\n"
            "• FAQ\n"
            "• Return to Main Menu"
        )

        send_text_message({
            "to": chat_id.split("@")[0],
            "type": "text",
            "messaging_product": "whatsapp",
            "text": {"body": summary_text}
        })

        time.sleep(1)

        # After the summary, send a quick FAQ list (via text or a very short list):
        faq_sections = [
            {
                "title": "Car Fumigation FAQ",
                "rows": [
                    { "id": "cfum_faq_safe",         "title": "Is it safe?",          "description": "Is fumigation safe for kids/pets?" },
                    { "id": "cfum_faq_included",     "title": "Service Details",      "description": "What’s included in our service?" },
                    { "id": "cfum_faq_warranty",     "title": "Warranty",             "description": "Coverage & terms" },
                    { "id": "cfum_faq_duration",     "title": "Service Duration",     "description": "How long does it take?" }
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
    # Fallback: no step matched → clear state & send Main Menu again
    # ────────────────────────────────────────────────────────────────────────────────
    clear_user_state("car", chat_id)
    send_main_menu(chat_id.split("@")[0])
    return Response(status=200)


# ────────────────────────────────────────────────────────────────────────────────
# 6) process_faq_response: When the user taps a “cfum_faq_*” row, send back answer
# ────────────────────────────────────────────────────────────────────────────────
def process_car_fumigation_faq_response(to: str, faq_id: str) -> None:
    """
    After the user taps one of the FAQ rows (id starts with "cfum_faq_"), we send
    the corresponding answer, then re-show the FAQ list.
    """
    faq_answers = {
        "cfum_faq_safe": (
            "Yes—our car-fumigation treatments are eco-friendly and safe for you, "
            "your family, and your pets.\n\n"
            "We only use NEA-approved chemicals and minimal odors.  "
            "Expect to drive your vehicle again in <1 hour after service."
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
            "Most sedans take about 20–30 minutes to fumigate.\n"
            "Larger SUVs/MPVs may take 30–45 minutes depending on size and condition."
        )
    }
    answer = faq_answers.get(faq_id, "Sorry, no info is available for that question.")
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": answer}
    })


# ────────────────────────────────────────────────────────────────────────────────
# 7) handle_car_fumigation_flow: Full flow handler
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
            return_data = send_vehicle_type_list(to_chat_id.split("@")[0])
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
            # Ask “Additional care fee?” (Yes/No as text prompt)
            return_data = send_additional_fee_prompt(to_chat_id.split("@")[0])
            return Response(status=200)

        # Step: “quote_summary” → they tapped one of the three buttons (“Book Now”, “FAQ”, “Return”)
        # or “additional_fee” → they typed “yes”/“no” and we proceed
        # We handle these in the BUTTON section below:
        pass

    # ─── B) If msg_type in ["button", "interactive"], handle the button payload
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        print(f"[DEBUG] handle_car_fumigation_flow: BUTTON payload='{payload}'")

        # A) When user clicks “help_pest” (actually handled by dispatcher), we already
        #    set state["step"] = "select_pest_type" and re-entered this function.

        # B) If they typed “yes”/“no” at the “additional_fee” step:
        if step == "additional_fee":
            payload_lower = payload.lower()

            if payload_lower in ["yes", "y", "no", "n"]:
                state["additional_fee_needed"] = (payload_lower.startswith("y"))
                set_user_state("car", to_chat_id, state)

                # Next → move to quote_summary
                state["step"] = "quote_summary"
                set_user_state("car", to_chat_id, state)
                return send_quote_summary(to_chat_id)

            # If they pressed nothing valid, re-prompt:
            send_text_message({
                "to": to_chat_id.split("@")[0],
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Please reply with Yes or No."}
            })
            return Response(status=200)

        # C) If they are on “quote_summary” and tapped “Book Now” / “FAQ” / “Return”
        if step == "quote_summary":
            pl = payload.lower()
            if pl == "book now":
                send_text_message({
                    "to": to_chat_id.split("@")[0],
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": {"body": "Great—Our agent will be in touch to schedule your appointment."}
                })
                clear_user_state("car", to_chat_id)
                return Response(status=200)

            if pl == "faq":
                # Re-show the FAQ list:
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

            if pl == "return to main menu":
                clear_user_state("car", to_chat_id)
                # Re-show the top-level main menu (template) via dispatcher helper:
                from helpers import send_template_message
                send_template_message(
                    to=to_chat_id.split("@")[0],
                    template_name="main_menu_v2",
                    template_params=["there"]
                )
                return Response(status=200)

            # Otherwise, fallback:
            send_text_message({
                "to": to_chat_id.split("@")[0],
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Sorry, I didn’t understand that. Type 'reset' to start over."}
            })
            return Response(status=200)

    # ─── C) If we fell through to here, it means no LIST matched, no BUTTON matched, no valid step:
    # Clear state and re-show main menu:
    clear_user_state("car", to_chat_id)
    from helpers import send_template_message
    send_template_message(
        to=to_chat_id.split("@")[0],
        template_name="main_menu_v2",
        template_params=["there"]
    )
    return Response(status=200)
