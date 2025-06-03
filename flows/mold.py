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

# Redis key prefix for Mold Remediation user states
MOLD_PREFIX = "mold"

# Internal alert numbers (without “+”) to ping when a user confirms
ALERT_NUMBERS = [
    "6587788080",  # Company number +65 8778 8080
    "6588662359",  # Bot number     +65 8866 2359
]

# Mold‐area options (titles & IDs)
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

# FAQ question → text mappings
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


# ─── 1) Mold Option Screen (buttons) ──────────────────────────────────────────

def send_mold_option_prompt(to: str, phone_number_id: str):
    """
    Shows: [Request a Quotation] / [More Info on Service] / [Return to Main Menu]
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
                    {"type": "reply", "reply": {"id": "return_main_menu", "title": "Return to Main Menu"}},
                ]
            }
        }
    }
    send_interactive_message(payload)


# ─── 2) FAQ List (interactive) ────────────────────────────────────────────────

def send_mold_removal_faq(to: str, phone_number_id: str):
    """
    Sends an interactive list of mold-related FAQs (similar to car_fumigation flow).
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
            "header": {"type": "text", "text": "Mold Removal FAQ"},
            "body": {"text": "Select a question to learn more:"},
            "footer": {"text": "Tap any question"},
            "action": {
                "button": "View FAQs",
                "sections": [{"title": "FAQ", "rows": rows}],
            },
        },
    }
    send_interactive_message(payload)


def process_mold_faq_response(to: str, faq_id: str):
    """
    Sends back the text answer for the given FAQ ID.
    """
    answer = MOLD_FAQ.get(faq_id, "Sorry, no information is available on that question.")
    send_text_message(to=to, body=answer)


# ─── 3) “Select Affected Area” List ───────────────────────────────────────────

def send_mold_area_selection(to: str, phone_number_id: str):
    """
    Presents the user with a list of MOLD_AREAS they have not yet reported.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    chosen_areas = state.get("affected_areas", [])

    # Filter out any already‐chosen titles
    available = [area for area in MOLD_AREAS if area["title"] not in chosen_areas]
    if not available:
        # If nothing left to choose, skip directly to growth location
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


# ─── 4) Bedroom & Bathroom Count Prompts ──────────────────────────────────────

def send_bedroom_count_prompt(to: str, phone_number_id: str):
    """
    After “Bedroom” is chosen, ask how many bedrooms are affected.
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
    After “Bathroom” is chosen, ask how many bathrooms are affected.
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


# ─── 5) “Add Another Area?” Confirmation ──────────────────────────────────────

def send_add_area_confirmation_prompt(to: str, phone_number_id: str):
    """
    After any area (other than Bedroom/Bathroom) is chosen, ask “Add another affected area?”
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


# ─── 6) “Mold Growth Location” Prompt ────────────────────────────────────────

def send_mold_growth_location(to: str, phone_number_id: str):
    """
    After all areas are reported, ask “Where did you see mold growth?” with a list.
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


# ─── 7) Final Summary & Confirmation ─────────────────────────────────────────

def send_mold_removal_summary(to: str, phone_number_id: str):
    """
    Summarize everything collected so far and ask “Yes” / “No” to confirm.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    # Build the textual summary from stored state
    lines = ["Summary of your mold removal request:\n", "Affected Areas Reported:"]
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


# ─── 8) Internal Alert + Ask for Photos ────────────────────────────────────────

def alert_internal_and_ask_photos(from_number: str):
    """
    1) Send an “🚨 New Mold Enquiry Booking 🚨” alert to ALERT_NUMBERS.
    2) Then prompt the user to upload wide-angle photos.
    """
    state = get_user_state(MOLD_PREFIX, from_number) or {}
    if not state:
        return

    # Build the alert body with plus‐sign phone format
    client_phone = f"+{from_number}"
    lines = [
        "🚨 New Mold Enquiry Booking 🚨",
        "",
        f"Client Phone Number: {client_phone}",
        "",
        "Affected Areas Reported:"
    ]
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

    alert_text = "\n".join(lines)

    # Send to both internal numbers
    for admin in ALERT_NUMBERS:
        send_text_message(to=admin, body=alert_text)

    # Now ask the user for photos
    photo_prompt = (
        "Hang tight—we’re bringing in a real, live human support agent for you!\n"
        "They’ll join the chat as soon as they’re available.\n\n"
        "In the meantime, could you please take a wide-angle photo (from the door) "
        "capturing the full room or area affected? This helps us provide a rough estimate "
        "ahead of time. Just upload the images here in this chat. 😊"
    )
    send_text_message(to=from_number, body=photo_prompt)

    # After the photo prompt, re-send the FAQ so they can browse it while waiting
    send_mold_removal_faq(
        to=from_number,
        phone_number_id=os.getenv("PHONE_NUMBER_ID")
    )

    # **Keep the state intact** so that once your agent joins, they can still access everything.
    # We do NOT clear the user state here, because the next step is your agent to handle the conversation.


# ─── 9) Main Flow Handler ─────────────────────────────────────────────────────

def handle_mold_flow(from_number: str, message: dict, user_state: dict):
    """
    Drives the entire Mold Remediation flow. Uses user_state["step"] to route
    list replies, quick‐reply buttons, and plain text through each stage.
    """
    state = user_state or {}
    step = state.get("step", "")
    msg_type = message.get("type")  # "text", "button", or "interactive"

    # Helper: extract quick‐reply button ID
    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"].get("payload", "")
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"]["id"]
        return ""

    # ─── FAQ Screen Handling (step == "mold_faq") ───────────────────────────────
    if step == "mold_faq":
        if msg_type in ["button", "interactive"]:
            payload = extract_button_payload(message)
            if payload and payload.startswith("mfaq_"):
                process_mold_faq_response(from_number, payload)
                # Re‐show FAQ so they can pick another question
                send_mold_removal_faq(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

    # ─── BUTTONS (quick‐reply) ────────────────────────────────────────────────────
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_mold_flow: BUTTON payload='{payload_lower}' from {from_number}")

            # Refresh state & step after possibly modifying it
            state = get_user_state(MOLD_PREFIX, from_number) or {}
            step = state.get("step", "")

            # 1) “Need help on Mold!” → show mold options
            if payload_lower == "need help on mold!":
                clear_user_state(MOLD_PREFIX, from_number)
                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(MOLD_PREFIX, from_number, new_state)
                send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # 2) step == "mold_option"
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
                    send_mold_removal_faq(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                if payload_lower == "return_main_menu":
                    clear_user_state(MOLD_PREFIX, from_number)
                    from flows.car_fumigation import send_main_menu
                    send_main_menu(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                # Fallback if unrecognized
                send_text_message(
                    to=from_number,
                    body="Sorry, I didn’t understand that. Type 'reset' to start over."
                )
                return

            # 3) step == "mold_waiting_add_area_confirmation"
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

            # 4) step == "mold_waiting_confirmation"
            if step == "mold_waiting_confirmation":
                if payload_lower == "mold_confirm_yes":
                    # (a) Alert internal numbers & ask for photos
                    alert_internal_and_ask_photos(from_number)

                    # We DO NOT clear the user state here—our human agent will pick up next.
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

    # ─── LIST Replies (interactive.list_reply) ─────────────────────────────────

    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_mold_flow: LIST payload='{selected_id}' from {from_number}")

        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        # A) step == "mold_select_area"
        if step == "mold_select_area":
            # “Other Areas”
            if selected_id == "area_others":
                state["step"] = "mold_waiting_other_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(
                    to=from_number,
                    body="Please specify the affected area not listed above:"
                )
                return

            # Otherwise, a normal area selection
            chosen = next((a for a in MOLD_AREAS if a["id"] == selected_id), None)
            if chosen:
                state.setdefault("affected_areas", []).append(chosen["title"])

            # If “Bedroom”
            if selected_id == "area_bedroom":
                state["step"] = "mold_waiting_bedroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bedroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # If “Bathroom”
            if selected_id == "area_bathroom":
                state["step"] = "mold_waiting_bathroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bathroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # Otherwise (living, store, kitchen, furniture, entire, smell, commercial)
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) step == "mold_waiting_bedroom_count"
        if step == "mold_waiting_bedroom_count":
            if selected_id.startswith("bedroom_count_"):
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
        if step == "mold_waiting_bathroom_count":
            if selected_id.startswith("bathroom_count_"):
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
                # A normal growth location (walls, ceiling, or both)
                state["growth_location"] = selected_id
                state["step"] = ""  # move on
                set_user_state(MOLD_PREFIX, from_number, state)
                send_mold_removal_summary(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # Otherwise (unhandled list)
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── Plain text handling (interactive free-text steps) ─────────────────────

    if msg_type == "text":
        text_body = message["text"]["body"].strip()
        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        print(f"[DEBUG] handle_mold_flow: TEXT at step='{step}' → '{text_body}' from {from_number}")

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
            state["step"] = ""  # move on
            set_user_state(MOLD_PREFIX, from_number, state)
            send_mold_removal_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # C) Anything else (unexpected text)
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── Fallback for unsupported payloads ─────────────────────────────────────

    print(f"[DEBUG] handle_mold_flow: Unsupported msg_type='{msg_type}' or step='{step}'")
    send_text_message(
        to=from_number,
        body="Sorry, I can’t handle that type of message. Type 'reset' to start over."
    )
    return
