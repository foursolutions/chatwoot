# flows/bedbug.py

import os
import time
from flask import Response

from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_interactive_message,
    send_template_message
)

# ────────────────────────────────────────────────────────────────────────────────
def send_bedbug_removal_faq(to: str) -> dict:
    header = "Bedbug Removal FAQ"
    body = "Select a FAQ question:"
    footer = "Tap an option"
    action_button = "Select FAQ"

    sections = [
        {
            "title": "FAQ Questions",
            "rows": [
                {"id": "bfq_safe",        "title": "Is it safe? Pets/Kids",   "description": "Are treatments safe?"},
                {"id": "bfq_included",    "title": "Service Details",          "description": "What's included in our service?"},
                {"id": "bfq_warranty",    "title": "Warranty Terms",           "description": "Coverage & terms"},
                {"id": "bfq_preparation", "title": "Preparation",              "description": "How to prepare your home?"},
                {"id": "bfq_duration",    "title": "Service Duration",         "description": "How long does it take?"},
                {"id": "bfq_payment",     "title": "Payment Options",          "description": "Payment methods accepted"}
            ]
        }
    ]

    payload = {
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {
                "button": action_button,
                "sections": sections
            }
        }
    }

    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_bedbug_removal_faq → {resp}")
    return resp


def process_bedbug_faq_response(to: str, faq_id: str) -> None:
    faq_answers = {
        "bfq_safe": (
            "Yes—our bedbug treatments are safe for kids and pets.\n\n"
            "We only use NEA-approved chemicals. We service homes, hospitals, hotels, etc."
        ),
        "bfq_included": (
            "Our bedbug service includes:\n"
            "• Furniture & flooring protection\n"
            "• Chemical spray and heat treatment\n"
            "• Post-service inspection within 7 days\n"
            "• Complimentary mattress encasement (if needed)"
        ),
        "bfq_warranty": (
            "We provide warranty coverage for 90 days. If bedbugs reappear within 90 days, "
            "we’ll re-treat at no extra cost (conditions apply)."
        ),
        "bfq_preparation": (
            "To prepare:\n"
            "• Wash all linens & clothes in hot water.\n"
            "• Vacuum and seal vacuum bag before disposal.\n"
            "• Remove clutter around bed and furniture.\n"
            "• Keep children and pets away until treatment is complete."
        ),
        "bfq_duration": (
            "A typical 3-bedroom apartment takes about 2–3 hours to treat. "
            "Larger homes may take longer depending on the infestation."
        ),
        "bfq_payment": (
            "We accept:\n"
            "• PayNow (UEN: 201812722M)\n"
            "• Online bank transfer\n"
            "• Cash on service (please prepare exact amount)"
        )
    }

    answer = faq_answers.get(faq_id, "Sorry, I don’t have information on that question.")
    send_text_message(to, answer)


def send_bedbug_option_prompt(to: str) -> dict:
    text = (
        "We’re happy to help with your bedbug removal!\n"
        "Please type:\n"
        "1️⃣ to Request a Quotation\n"
        "2️⃣ for More Info on Service\n"
        "3️⃣ to Return to Main Menu"
    )
    resp = send_text_message(to, text)
    print(f"[DEBUG] send_bedbug_option_prompt(text) → {resp}")
    return resp


def send_bedbug_area_selection(to: str) -> dict:
    header = "Select Infested Areas"
    body = "Which area is affected by bedbugs? (Choose one at a time.)"
    footer = "Select Area"
    action_button = "Select Area"

    sections = [
        {
            "title": "Affected Area",
            "rows": [
                {"id": "area_bedroom", "title": "Bedroom", "description": "Bed, Mattress"},
                {"id": "area_living", "title": "Living Room", "description": "Sofa, Carpets"},
                {"id": "area_sofa", "title": "Sofa Only", "description": "Just the sofa"},
                {"id": "area_mattress", "title": "Mattress Only", "description": "Just the mattress"},
                {"id": "area_others", "title": "Others", "description": "Other furniture"}
            ]
        }
    ]

    payload = {
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {
                "button": action_button,
                "sections": sections
            }
        }
    }

    resp = send_interactive_message(payload)
    print(f"[DEBUG] send_bedbug_area_selection → {resp}")
    return resp


def handle_bedbug_flow(from_number: str, message: dict, user_state: dict) -> Response:
    state = user_state or {}
    step = state.get("step", "")
    msg_type = message.get("type")

    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"].get("payload", "")
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"].get("id", "")
        return ""

    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_bedbug_flow: LIST payload='{choice_id}'")

        if step == "bedbug_faq":
            process_bedbug_faq_response(from_number, choice_id)
            send_bedbug_removal_faq(to=from_number)
            return Response(status=200)

        if step == "bedbug_select_area":
            state.setdefault("affected_areas", []).append(
                message["interactive"]["list_reply"].get("title", "")
            )
            set_user_state("bedbug", from_number, state)
            state["step"] = "bedbug_waiting_add_area_confirmation"
            set_user_state("bedbug", from_number, state)
            send_text_message(from_number, "Would you like to add another infested area? (Yes or No)")
            return Response(status=200)

    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message).lower()
        print(f"[DEBUG] handle_bedbug_flow: BUTTON payload='{payload}'")

        if payload == "need help on bedbug!":
            clear_user_state("bedbug", from_number)
            set_user_state("bedbug", from_number, {"step": "bedbug_option", "affected_areas": []})
            return send_bedbug_option_prompt(to=from_number)

        if step == "bedbug_option":
            if payload in ["1", "1️⃣"]:
                set_user_state("bedbug", from_number, {"step": "bedbug_select_area", "affected_areas": []})
                return send_bedbug_area_selection(to=from_number)
            if payload in ["2", "2️⃣"]:
                state["step"] = "bedbug_faq"
                set_user_state("bedbug", from_number, state)
                return send_bedbug_removal_faq(to=from_number)
            if payload in ["3", "3️⃣"]:
                clear_user_state("bedbug", from_number)
                send_template_message(from_number, "main_menu_v2", ["there"])
                return Response(status=200)
            send_text_message(from_number, "Please enter 1, 2, or 3.")
            return Response(status=200)

        if step == "bedbug_waiting_add_area_confirmation":
            if payload in ["yes", "y"]:
                state["step"] = "bedbug_select_area"
                set_user_state("bedbug", from_number, state)
                return send_bedbug_area_selection(to=from_number)
            if payload in ["no", "n"]:
                summary = "Bedbug Removal Summary:\n\n"
                for idx, area in enumerate(state.get("affected_areas", []), start=1):
                    summary += f"{idx}.) {area}\n"
                summary += "\nType 'Confirm' to book now, or 'Return' to go back to the main menu."
                send_text_message(from_number, summary)
                state["step"] = "bedbug_waiting_confirmation"
                set_user_state("bedbug", from_number, state)
                return Response(status=200)
            send_text_message(from_number, "Please reply Yes or No.")
            return Response(status=200)

        if step == "bedbug_waiting_confirmation":
            if payload == "confirm":
                send_text_message(from_number, "Thanks—Your booking request has been sent to our agent. You’ll hear from us soon.")
                clear_user_state("bedbug", from_number)
                return Response(status=200)
            if payload == "return":
                clear_user_state("bedbug", from_number)
                send_template_message(from_number, "main_menu_v2", ["there"])
                return Response(status=200)
            send_text_message(from_number, "Please type 'Confirm' or 'Return'.")
            return Response(status=200)

    clear_user_state("bedbug", from_number)
    send_template_message(from_number, "main_menu_v2", ["there"])
    return Response(status=200)
