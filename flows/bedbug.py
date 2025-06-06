# flows/bedbug.py

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
# send_bedbug_removal_faq: Step 1 of Bedbug flow (FAQ)
# ────────────────────────────────────────────────────────────────────────────────
def send_bedbug_removal_faq(to: str) -> dict:
    """
    Sends an interactive FAQ list for Bedbug Removal.
    """
    header = "Bedbug Removal FAQ"
    body = "Select a FAQ question:"
    footer = "Tap an option"
    action_button = "Select FAQ"

    sections = [
        {
            "title": "FAQ Questions",
            "rows": [
                {"id": "bfq_safe",        "title": "Is it safe? Pets/Kids",   "description": "Are treatments safe?"                 },
                {"id": "bfq_included",    "title": "Service Details",          "description": "What's included in our service?"      },
                {"id": "bfq_warranty",    "title": "Warranty Terms",           "description": "Coverage & terms"                     },
                {"id": "bfq_preparation", "title": "Preparation",              "description": "How to prepare your home?"            },
                {"id": "bfq_duration",    "title": "Service Duration",         "description": "How long does it take?"               },
                {"id": "bfq_payment",     "title": "Payment Options",          "description": "Payment methods accepted"             }
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
    print(f"[DEBUG] send_bedbug_removal_faq → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# process_bedbug_faq_response: After user taps a bfq_ row, send answer
# ────────────────────────────────────────────────────────────────────────────────
def process_bedbug_faq_response(to: str, faq_id: str) -> None:
    """
    After the user taps one of the FAQ rows (id starts with "bfq_"), we send back answer,
    then re-render the FAQ list.
    """
    faq_answers = {
        "bfq_safe": (
            "Yes—our bedbug treatments are safe for kids and pets.\n\n"
            "We only use NEA-approved chemicals.  We service homes, hospitals, hotels, etc."
        ),
        "bfq_included": (
            "Our bedbug service includes:\n"
            "• Furniture & flooring protection\n"
            "• Chemical spray and heat treatment\n"
            "• Post-service inspection within 7 days\n"
            "• Complimentary mattress encasement (if needed)\n"
        ),
        "bfq_warranty": (
            "We provide warranty coverage for 90 days.  If bedbugs reappear within 90 days, "
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
            "• Cash on service (please prepare exact amount)\n"
        )
    }

    answer = faq_answers.get(faq_id, "Sorry, I don’t have information on that question.")
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": answer}
    })


# ────────────────────────────────────────────────────────────────────────────────
# send_bedbug_option_prompt: Step 2: “Request Quote / More Info / Return”
# ────────────────────────────────────────────────────────────────────────────────
def send_bedbug_option_prompt(to: str) -> dict:
    """
    “Would you like to: Request a Quotation / More Info on Service / Return to Main Menu?”
    We’ll just send a plain text that says “Reply 1, 2, or 3,” or you can send a two-button interactive.
    For simplicity, we do plain text instructions:
    """
    text = (
        "We’re happy to help with your bedbug removal!\n"
        "Please type:\n"
        "1️⃣ to Request a Quotation\n"
        "2️⃣ for More Info on Service\n"
        "3️⃣ to Return to Main Menu"
    )
    resp = send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": text}
    })
    print(f"[DEBUG] send_bedbug_option_prompt(text) → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# send_bedbug_area_selection: Step 3: show “Which room is affected?” list
# ────────────────────────────────────────────────────────────────────────────────
def send_bedbug_area_selection(to: str) -> dict:
    """
    List common areas/rooms (Bedroom, Living Room, Sofa, Mattress, etc.) via a list.
    """
    header = "Select Infested Areas"
    body = "Which area is affected by bedbugs? (Choose one at a time.)"
    footer = "Select Area"
    action_button = "Select Area"

    sections = [
        {
            "title": "Affected Area",
            "rows": [
                {"id": "area_bedroom", "title": "Bedroom",       "description": "Bed, Mattress"    },
                {"id": "area_living",  "title": "Living Room",   "description": "Sofa, Carpets"    },
                {"id": "area_sofa",    "title": "Sofa Only",     "description": "Just the sofa"    },
                {"id": "area_mattress","title": "Mattress Only", "description": "Just the mattress"},
                {"id": "area_others",  "title": "Others",        "description": "Other furniture"}
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
    print(f"[DEBUG] send_bedbug_area_selection → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# handle_bedbug_flow: Full Bedbug flow handler
# ────────────────────────────────────────────────────────────────────────────────
def handle_bedbug_flow(
    from_number: str,
    message: dict,
    user_state: dict
) -> Response:
    """
    Drives the entire Bedbug Removal flow. We check user_state["step"], msg_type,
    and route accordingly.
    """
    state = user_state or {}
    step  = state.get("step", "")
    msg_type = message.get("type")  # "chat", "button", or "interactive"

    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"].get("payload", "")
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"].get("id", "")
        return ""

    # ── A) If they tapped a LIST item while in “faq” step:
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_bedbug_flow: LIST payload='{choice_id}'")

        if step == "bedbug_faq":
            process_bedbug_faq_response(from_number, choice_id)
            # Re-show the FAQ afterwards:
            send_bedbug_removal_faq(to=from_number)
            return Response(status=200)

        if step == "bedbug_select_area":
            state.setdefault("affected_areas", []).append(
                message["interactive"]["list_reply"].get("title", "")
            )
            set_user_state("bedbug", from_number, state)

            # After they pick “Bedroom” or “Sofa” – we ask them to “Add another?”:
            state["step"] = "bedbug_waiting_add_area_confirmation"
            set_user_state("bedbug", from_number, state)

            resp = send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Would you like to add another infested area? (Yes or No)"}
            })
            return Response(status=200)

        # (You can add more list replies if needed—for brevity, this covers the main cases.)

    # ── B) If they tapped a BUTTON (type=="button" or "interactive" button_reply):
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message).lower()
        print(f"[DEBUG] handle_bedbug_flow: BUTTON payload='{payload}'")

        # 1) If from the main menu they tapped “Need help on Bedbug!”:
        if payload == "need help on bedbug!":
            clear_user_state("bedbug", from_number)
            new_state = {"step": "bedbug_option", "affected_areas": []}
            set_user_state("bedbug", from_number, new_state)
            return send_bedbug_option_prompt(to=from_number)

        # 2) If we are on the “bedbug_option” step:
        if step == "bedbug_option":
            if payload == "1️⃣" or payload == "1":
                # Request a Quotation
                new_state = {"step": "bedbug_select_area", "affected_areas": []}
                set_user_state("bedbug", from_number, new_state)
                return send_bedbug_area_selection(to=from_number)

            if payload == "2️⃣" or payload == "2":
                # More Info → show FAQ
                state["step"] = "bedbug_faq"
                set_user_state("bedbug", from_number, state)
                return send_bedbug_removal_faq(to=from_number)

            if payload == "3️⃣" or payload == "3":
                # Return to Main Menu:
                clear_user_state("bedbug", from_number)
                from helpers import send_template_message
                send_template_message(
                    to=from_number,
                    template_name="main_menu_v2",
                    template_params=["there"]
                )
                return Response(status=200)

            # Fallback if they tapped something else:
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Please enter 1, 2, or 3."}
            })
            return Response(status=200)

        # 3) If we are waiting for “Yes/No” to add another area:
        if step == "bedbug_waiting_add_area_confirmation":
            if payload in ["yes", "y"]:
                state["step"] = "bedbug_select_area"
                set_user_state("bedbug", from_number, state)
                return send_bedbug_area_selection(to=from_number)

            if payload in ["no", "n"]:
                # Summarize and confirm booking:
                summary = "Bedbug Removal Summary:\n\n"
                for idx, area in enumerate(state.get("affected_areas", []), start=1):
                    summary += f"{idx}.) {area}\n"
                summary += (
                    "\nType 'Confirm' to book now, or 'Return' to go back to the main menu."
                )
                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": {"body": summary}
                })
                state["step"] = "bedbug_waiting_confirmation"
                set_user_state("bedbug", from_number, state)
                return Response(status=200)

            # If invalid:
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Please reply Yes or No."}
            })
            return Response(status=200)

        # 4) If they are on “bedbug_waiting_confirmation”:
        if step == "bedbug_waiting_confirmation":
            if payload == "confirm":
                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": {"body": "Thanks—Your booking request has been sent to our agent. You’ll hear from us soon."}
                })
                clear_user_state("bedbug", from_number)
                return Response(status=200)

            if payload == "return":
                clear_user_state("bedbug", from_number)
                from helpers import send_template_message
                send_template_message(
                    to=from_number,
                    template_name="main_menu_v2",
                    template_params=["there"]
                )
                return Response(status=200)

            # Fallback:
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Please type 'Confirm' or 'Return'."}
            })
            return Response(status=200)

    # ── C) FALLBACK if we get here, no matching step or type:
    clear_user_state("bedbug", from_number)
    from helpers import send_template_message
    send_template_message(
        to=from_number,
        template_name="main_menu_v2",
        template_params=["there"]
    )
    return Response(status=200)
