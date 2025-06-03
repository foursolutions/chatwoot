# flows/mold.py

import os
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_interactive_message,
)

# ─── Constants & Static Data ────────────────────────────────────────────────

# Redis key prefix
MOLD_PREFIX = "mold"

# Numbers to alert when a user confirms (no “+” in front)
ALERT_NUMBERS = [
    "6587788080",  # Company alert number: +65 8778 8080
    "6588662359",  # Bot number:            +65 8866 2359
]

# Mold-Area definitions
MOLD_AREAS = [
    {"id": "area_bedroom",    "title": "Bedroom",       "description": "Mold in bedroom(s)"},
    {"id": "area_bathroom",   "title": "Bathroom",      "description": "Mold in bathroom(s)"},
    {"id": "area_store",      "title": "Store/Yard",    "description": "Store room / Service yard"},
    {"id": "area_living",     "title": "Living Area",   "description": "Mold in living/dining"},
    {"id": "area_kitchen",    "title": "Kitchen",       "description": "Mold in kitchen"},
    {"id": "area_furniture",  "title": "Furniture",     "description": "Mold on furniture"},
    {"id": "area_entire",     "title": "Entire Unit",   "description": "Whole unit affected"},
    {"id": "area_smell",      "title": "Mold Smell",    "description": "Odor detected"},
    {"id": "area_commercial", "title": "Commercial",    "description": "Office / Shop affected"},
    {"id": "area_others",     "title": "Other Areas",   "description": "Unlisted areas"},
]

# FAQ question → answer mapping
MOLD_FAQ = {
    "mfaq_safe": (
        "Yes, our mold removal and anti-mold painting treatments are safe for children and pets.\n\n"
        "We frequently service sensitive environments such as schools, laboratories, and hospitals. "
        "The anti-mold paint we use is odorless, ensuring minimal odor after completion."
    ),
    "mfaq_included": (
        "Our mold removal service includes:\n"
        "• Protection of flooring, furniture, and fittings to minimize post-service cleanup.\n"
        "• Chemical remediation: direct application, scrubbing, and removal of dead mold.\n"
        "• Complimentary removal of booklice if discovered (NEA-licensed Vector Operator).\n"
        "• Application of two coats of odorless, white anti-mold paint to prevent future mold growth."
    ),
    "mfaq_warranty": (
        "We provide warranty coverage for all mold removal services to ensure lasting effectiveness. "
        "Warranty terms typically range from 6 to 12 months, depending on the package:\n"
        "• One complimentary inspection before warranty expiry (appointment required).\n"
        "• One-time complimentary mold removal during the warranty period if mold reappears.\n"
        "Note: External factors like active water leakage are not covered under warranty."
    ),
    "mfaq_preparation": (
        "To ensure a smooth service experience, please prepare the space by following these guidelines:\n"
        "• Limit the number of people in areas scheduled for treatment.\n"
        "• Remove loose items and personal belongings from treatment areas.\n"
        "• Remove curtains from windows in rooms scheduled for service.\n"
        "• Ensure access to equipment (ladders, fans, AC, floor mats) if needed.\n"
        "• Inform our technician on the day if there are concealed areas (e.g., cabinets).\n"
        "• Relocate heavy or sensitive items, as we may not be able to move them safely.\n"
        "Note: We aim to arrive within 1 hour of the scheduled time; any delays will be communicated."
    ),
    "mfaq_duration": (
        "Typical service durations are as follows:\n"
        "• Bedroom: 2–5 hours\n"
        "• Bathroom: 1–3 hours\n"
        "• Multiple areas: Technician will advise after inspection.\n"
        "Actual times may vary based on drying times, weather, and the size of the area."
    ),
    "mfaq_payment": (
        "We accept the following payment methods:\n"
        "• PayNow: Payment via UEN 201812722M\n"
        "• Atome: Interest-free installment plan for 3 months (5% surcharge applies)\n"
        "• Cash: Please inform us in advance if you need to pay in cash and prepare the exact amount."
    ),
}


# ─── 1) “Mold Option” Menu ───────────────────────────────────────────────

def send_mold_option_prompt(to: str, phone_number_id: str):
    """
    Shows three quick‐reply buttons: “Request a Quotation”, “More Info on Service”, “Return to Main Menu”.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "We are happy to help! Select an option below for us to better understand what you are looking for!"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "mold_get_quote", "title": "Request a Quotation"}},
                    {"type": "reply", "reply": {"id": "mold_more_info", "title": "More Info on Service"}},
                    {"type": "reply", "reply": {"id": "return_main_menu", "title": "Return to Main Menu"}}
                ]
            }
        }
    }
    send_interactive_message(payload)


# ─── 2) “Mold Removal FAQ” Interactive List ─────────────────────────────

def send_mold_removal_faq_with_header(to: str):
    """
    Sends an interactive list of FAQs for mold removal, placing a custom header that
    says “While you wait, here’s our FAQ to learn more about our mold removal service:”.
    """
    rows = [
        {"id": "mfaq_safe",        "title": "Is it safe? Kids/Pets",     "description": ""},
        {"id": "mfaq_included",    "title": "What’s included?",          "description": ""},
        {"id": "mfaq_warranty",    "title": "Do you provide a warranty?", "description": ""},
        {"id": "mfaq_preparation", "title": "How should I prepare?",     "description": ""},
        {"id": "mfaq_duration",    "title": "How long will it take?",    "description": ""},
        {"id": "mfaq_payment",     "title": "Payment options",            "description": ""},
    ]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            # Embed the “While you wait…” text in the header
            "header": {
                "type": "text",
                "text": (
                    "While you wait, here’s our FAQ to learn more about our mold removal service:"
                )
            },
            # The body prompt can be brief, e.g. “Select a question to learn more:”
            "body": {"text": "Select a question to learn more:"},
            "footer": {"text": ""},
            "action": {
                "button": "View FAQs",
                "sections": [{"title": "FAQ", "rows": rows}],
            },
        },
    }
    send_interactive_message(payload)


def process_mold_faq_response(to: str, faq_id: str):
    """
    Sends the answer text corresponding to the FAQ ID selected by the user.
    """
    answer = MOLD_FAQ.get(faq_id, "Sorry, I don’t have information on that question.")
    send_text_message(to=to, body=answer)


# ─── 3) “Select Affected Area” (List) ────────────────────────────────────

def send_mold_area_selection(to: str, phone_number_id: str):
    """
    Shows an interactive list of all mold-affected areas not yet reported by the user.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    chosen_areas = state.get("affected_areas", [])

    available = [area for area in MOLD_AREAS if area["title"] not in chosen_areas]
    if not available:
        # If none remain, skip straight to growth location
        send_mold_growth_location(to, phone_number_id)
        return

    rows = [{"id": a["id"], "title": a["title"], "description": a["description"]} for a in available]
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Mold Affected Areas"},
            "body": {"text": "Please select an area affected by mold (one at a time):"},
            "footer": {"text": "Choose one"},
            "action": {
                "button": "Select Area",
                "sections": [{"title": "Affected Areas", "rows": rows}],
            },
        },
    }
    send_interactive_message(payload)

    state["step"] = "mold_select_area"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 4) Bedroom / Bathroom Count Prompts ─────────────────────────────────

def send_bedroom_count_prompt(to: str, phone_number_id: str):
    """
    Asks “How many bedrooms are affected?” if the user has chosen “Bedroom”.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Number of Bedrooms Affected"},
            "body": {"text": "How many bedrooms are affected?"},
            "footer": {"text": "Select an option"},
            "action": {
                "button": "Select Count",
                "sections": [{
                    "title": "Bedrooms",
                    "rows": [
                        {"id": "bedroom_count_1", "title": "1 bedroom",  "description": ""},
                        {"id": "bedroom_count_2", "title": "2 bedrooms", "description": ""},
                        {"id": "bedroom_count_3", "title": "3+ bedrooms", "description": ""}
                    ]
                }]
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bedroom_count"
    set_user_state(MOLD_PREFIX, to, state)


def send_bathroom_count_prompt(to: str, phone_number_id: str):
    """
    Asks “How many bathrooms are affected?” if the user has chosen “Bathroom”.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Number of Bathrooms Affected"},
            "body": {"text": "How many bathrooms are affected?"},
            "footer": {"text": "Select an option"},
            "action": {
                "button": "Select Count",
                "sections": [{
                    "title": "Bathrooms",
                    "rows": [
                        {"id": "bathroom_count_1", "title": "1 bathroom",  "description": ""},
                        {"id": "bathroom_count_2", "title": "2 bathrooms", "description": ""},
                        {"id": "bathroom_count_3", "title": "3+ bathrooms", "description": ""}
                    ]
                }]
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bathroom_count"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 5) “Add Another Affected Area?” Confirmation ────────────────────────

def send_add_area_confirmation_prompt(to: str, phone_number_id: str):
    """
    After a non‐countable area is chosen, ask “Would you like to add another affected area?”
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Would you like to add another affected area?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "add_area_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "add_area_no",  "title": "No"}}
                ]
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_add_area_confirmation"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 6) “Mold Growth Location” Prompt ────────────────────────────────────

def send_mold_growth_location(to: str, phone_number_id: str):
    """
    After all areas are reported, ask “Where did you see mold growth?” (Walls/Ceiling/Both/Others).
    """
    rows = [
        {"id": "growth_walls",   "title": "Walls only",        "description": ""},
        {"id": "growth_ceiling", "title": "Ceiling only",      "description": ""},
        {"id": "growth_both",    "title": "Walls & ceiling",   "description": ""},
        {"id": "growth_others",  "title": "Other (specify)",   "description": ""}
    ]
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Mold Growth Location"},
            "body": {"text": "Where is the mold growth primarily located?"},
            "footer": {"text": "Choose one"},
            "action": {
                "button": "Select Location",
                "sections": [{"title": "Growth Options", "rows": rows}],
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_growth_location"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 7) Final Summary & Confirmation ────────────────────────────────────

def send_mold_removal_summary(to: str, phone_number_id: str):
    """
    Summarizes all collected data so far, then prompts “Yes” or “No” to confirm.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    lines = ["Summary of your mold removal request:\n", "Affected Areas Reported:"]
    for idx, a in enumerate(state.get("affected_areas", []), start=1):
        lines.append(f"{idx}.) {a}")

    if "bedroom_count" in state:
        lines.append(f"\nBedrooms affected: {state['bedroom_count']}")
    if "bathroom_count" in state:
        lines.append(f"Bathrooms affected: {state['bathroom_count']}")

    if "growth_location" in state:
        growth_map = {
            "growth_ceiling": "Ceiling only",
            "growth_walls":   "Walls only",
            "growth_both":    "Walls & ceiling"
        }
        chosen = growth_map.get(state["growth_location"], state["growth_location"])
        lines.append(f"\nGrowth Location: {chosen}")

    body_text = "\n".join(lines) + "\n\nSelect 'Yes' or 'No' to confirm."

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "mold_confirm_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "mold_confirm_no",  "title": "No"}}
                ]
            }
        }
    }
    send_interactive_message(payload)

    state["step"] = "mold_waiting_confirmation"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 8) Internal Alert + Photo Prompt + FAQ ───────────────────────────────

def alert_internal_and_ask_photos(from_number: str):
    """
    1) Send an alert ("🚨 New Mold Enquiry Booking 🚨") to ALERT_NUMBERS.
    2) Prompt the user to upload wide-angle photos.
    3) Immediately send a single interactive list whose header reads:
       “While you wait, here’s our FAQ to learn more about our mold removal service:”
       so that the FAQ cannot be overlooked.
    """
    state = get_user_state(MOLD_PREFIX, from_number) or {}
    if not state:
        return

    # Build the alert text
    client_phone = f"+{from_number}"
    lines = [
        "🚨 New Mold Enquiry Booking 🚨",
        "",
        f"Client Phone Number: {client_phone}",
        "",
        "Affected Areas Reported:"
    ]
    for idx, area in enumerate(state.get("affected_areas", []), start=1):
        lines.append(f"{idx}.) {area}")

    if "bedroom_count" in state:
        lines.append(f"\nBedrooms affected: {state['bedroom_count']}")
    if "bathroom_count" in state:
        lines.append(f"Bathrooms affected: {state['bathroom_count']}")

    if "growth_location" in state:
        growth_map = {
            "growth_ceiling": "Ceiling only",
            "growth_walls":   "Walls only",
            "growth_both":    "Walls & ceiling"
        }
        chosen = growth_map.get(state["growth_location"], state["growth_location"])
        lines.append(f"\nGrowth Location: {chosen}")

    alert_text = "\n".join(lines)

    # 1) Send the alert to each admin number
    for admin in ALERT_NUMBERS:
        send_text_message(to=admin, body=alert_text)

    # 2) Prompt the user for photos, with the updated “Hang tight…” copy
    photo_prompt = (
        "Hang tight—we’re bringing in a real, live human support agent for you!\n"
        "They’ll join the chat as soon as they’re available.\n\n"
        "In the meantime, could you please take a wide-angle photo (from the door) "
        "capturing the full room or area affected? This helps us provide a rough estimate "
        "ahead of time. Just upload the images here in this chat. 😊"
    )
    send_text_message(to=from_number, body=photo_prompt)

    # 3) Now send a single interactive list whose header already says “While you wait…”
    send_mold_removal_faq_with_header(to=from_number)

    # We deliberately keep state intact so that your live agent can pick up the conversation next.


# ─── 9) Main Flow Handler ───────────────────────────────────────────────

def handle_mold_flow(from_number: str, message: dict, user_state: dict):
    """
    Drives the entire mold-remediation flow. Routes each incoming message
    (text, button, or interactive list reply) based on user_state["step"].
    """
    state = user_state or {}
    step = state.get("step", "")
    msg_type = message.get("type")  # "text", "button", or "interactive"

    # Helper to extract a quick‐reply button ID
    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"].get("payload", "")
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"]["id"]
        return ""

    # ─── 1) FAQ Screen Handling ─────────────────────────────────────────
    if step == "mold_faq":
        if msg_type in ["button", "interactive"]:
            payload = extract_button_payload(message)
            if payload and payload.startswith("mfaq_"):
                process_mold_faq_response(from_number, payload)
                # Show FAQ again if they want to pick another question
                send_mold_removal_faq_with_header(to=from_number)
                return

    # ─── 2) BUTTONS (Quick‐Reply) ───────────────────────────────────────
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_mold_flow: BUTTON payload='{payload_lower}'")

            # Refresh state (in case it changed just now)
            state = get_user_state(MOLD_PREFIX, from_number) or {}
            step = state.get("step", "")

            # A) “Need help on Mold!” → Show the “mold_option” menu
            if payload_lower == "need help on mold!":
                clear_user_state(MOLD_PREFIX, from_number)
                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(MOLD_PREFIX, from_number, new_state)
                send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # B) step == "mold_option"
            if step == "mold_option":
                if payload_lower == "mold_get_quote":
                    new_state = {"step": "mold_select_area", "affected_areas": []}
                    set_user_state(MOLD_PREFIX, from_number, new_state)
                    send_mold_area_selection(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                if payload_lower == "mold_more_info":
                    state["step"] = "mold_faq"
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_removal_faq_with_header(to=from_number)
                    return

                if payload_lower == "return_main_menu":
                    clear_user_state(MOLD_PREFIX, from_number)
                    from flows.car_fumigation import send_main_menu
                    send_main_menu(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                # Fallback
                send_text_message(
                    to=from_number,
                    body="Sorry, I didn’t understand that. Type 'reset' to start over."
                )
                return

            # C) step == "mold_waiting_add_area_confirmation"
            if step == "mold_waiting_add_area_confirmation":
                if payload_lower == "add_area_yes":
                    state["step"] = "mold_select_area"
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_area_selection(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                elif payload_lower == "add_area_no":
                    state["step"] = "mold_prompt_growth"
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_growth_location(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                else:
                    send_text_message(to=from_number, body="Please select 'Yes' or 'No'.")
                    return

            # D) step == "mold_waiting_confirmation"
            if step == "mold_waiting_confirmation":
                if payload_lower == "mold_confirm_yes":
                    # (1) Internal alert  (2) Photo prompt  (3) FAQ list embedded
                    alert_internal_and_ask_photos(from_number)
                    return

                elif payload_lower == "mold_confirm_no":
                    send_text_message(
                        to=from_number,
                        body="Let's update your mold details. Please select 'Request a Quotation' to restart."
                    )
                    clear_user_state(MOLD_PREFIX, from_number)
                    return
                else:
                    send_text_message(to=from_number, body="Please select 'Yes' or 'No'.")
                    return

            # Fallback
            send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
            return

    # ─── 3) LIST Replies (interactive.list_reply) ─────────────────────────
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_mold_flow: LIST payload='{selected_id}'")

        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        # A) step == "mold_select_area"
        if step == "mold_select_area":
            if selected_id == "area_others":
                state["step"] = "mold_waiting_other_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(
                    to=from_number,
                    body="Please specify the affected area not listed above:"
                )
                return

            chosen = next((a for a in MOLD_AREAS if a["id"] == selected_id), None)
            if chosen:
                state.setdefault("affected_areas", []).append(chosen["title"])

            if selected_id == "area_bedroom":
                state["step"] = "mold_waiting_bedroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bedroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            if selected_id == "area_bathroom":
                state["step"] = "mold_waiting_bathroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bathroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # Otherwise (e.g. living, store, kitchen, etc.)
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) step == "mold_waiting_bedroom_count"
        if step == "mold_waiting_bedroom_count" and selected_id.startswith("bedroom_count_"):
            count = selected_id.split("_")[-1]
            state["bedroom_count"] = count
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # C) step == "mold_waiting_bathroom_count"
        if step == "mold_waiting_bathroom_count" and selected_id.startswith("bathroom_count_"):
            count = selected_id.split("_")[-1]
            state["bathroom_count"] = count
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # D) step == "mold_waiting_growth_location"
        if step == "mold_waiting_growth_location":
            if selected_id == "growth_others":
                state["step"] = "mold_waiting_growth_other"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(
                    to=from_number,
                    body="Please specify the mold growth location not listed above:"
                )
                return
            else:
                state["growth_location"] = selected_id
                state["step"] = ""  # move on to summary
                set_user_state(MOLD_PREFIX, from_number, state)
                send_mold_removal_summary(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # Fallback
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── 4) Plain Text Handling ─────────────────────────────────────────────

    if msg_type == "text":
        text_body = message["text"]["body"].strip()
        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        print(f"[DEBUG] handle_mold_flow: TEXT at step='{step}' → '{text_body}'")

        # A) step == "mold_waiting_other_area"
        if step == "mold_waiting_other_area":
            state.setdefault("affected_areas", []).append("Other: " + text_body)
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) step == "mold_waiting_growth_other"
        if step == "mold_waiting_growth_other":
            state["growth_location"] = text_body
            state["step"] = ""  # move on to summary
            set_user_state(MOLD_PREFIX, from_number, state)
            send_mold_removal_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # Fallback
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── 5) Fallback if we reach here ─────────────────────────────────────
    print(f"[DEBUG] handle_mold_flow: Unsupported msg_type='{msg_type}' or step='{step}'")
    send_text_message(
        to=from_number,
        body="Sorry, I can’t handle that type of message. Type 'reset' to start over."
    )
    return
