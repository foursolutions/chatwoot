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

# Redis key prefix for Mold Remediation
MOLD_PREFIX = "mold"

# Numbers to alert when a user confirms (“+65 8778 8080” and “+65 8866 2359”),
# but stored without the “+” for send_text_message(…)
ALERT_NUMBERS = [
    "6587788080",  # Company alert number
    "6588662359",  # Bot number (for logging/record)
]

# Mold‐area definitions that users can pick, one at a time.
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


# ─── 1) “Mold Option” Menu ──────────────────────────────────────────────────

def send_mold_option_prompt(to: str, phone_number_id: str):
    """
    Displays three quick‐reply buttons:
    [Request a Quotation], [More Info on Service], [Return to Main Menu].
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


# ─── 2) “Mold Removal FAQ” List (with Header in Body) ──────────────────────

def send_mold_removal_faq_with_body_header(to: str):
    """
    Sends an interactive FAQ list for mold removal, placing our “While you wait…” text
    in the body. Because WhatsApp truncates or hides long header text, we move it here.
    """
    rows = [
        {"id": "mfaq_safe",        "title": "Is it safe? Kids/Pets",     "description": ""},
        {"id": "mfaq_included",    "title": "What’s included?",          "description": ""},
        {"id": "mfaq_warranty",    "title": "Do you provide a warranty?", "description": ""},
        {"id": "mfaq_preparation", "title": "How should I prepare?",     "description": ""},
        {"id": "mfaq_duration",    "title": "How long will it take?",    "description": ""},
        {"id": "mfaq_payment",     "title": "Payment options",            "description": ""},
    ]

    # Place the “While you wait...” sentence into the interactive body text, followed by a blank line
    # and then a simple “Select a question to learn more:” prompt.
    body_text = (
        "While you wait, here’s our FAQ to learn more about our mold removal service:\n\n"
        "Select a question to learn more:"
    )

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            # We use a short header title so WhatsApp will definitely render it.
            "header": {"type": "text", "text": "Mold Removal FAQ"},
            "body": {"text": body_text},
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
    Sends the appropriate answer text when the user selects any mfaq_* row.
    """
    answer = MOLD_FAQ.get(faq_id, "Sorry, I don’t have information on that question.")
    send_text_message(to=to, body=answer)


# ─── 3) “Select Affected Area” (Interactive List) ─────────────────────────

def send_mold_area_selection(to: str, phone_number_id: str):
    """
    Shows all mold‐affected areas that haven’t yet been reported by this user.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    chosen_areas = state.get("affected_areas", [])

    # Filter out any titles the user has already picked
    available = [area for area in MOLD_AREAS if area["title"] not in chosen_areas]
    if not available:
        # If there are no more areas left, skip straight to asking for growth location
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


# ─── 4) “Bedroom / Bathroom Count” Prompts ───────────────────────────────

def send_bedroom_count_prompt(to: str, phone_number_id: str):
    """
    After the user selects “Bedroom,” ask how many bedrooms are affected.
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
                        {"id": "bedroom_count_1", "title": "1 bedroom",   "description": ""},
                        {"id": "bedroom_count_2", "title": "2 bedrooms",  "description": ""},
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
    After the user selects “Bathroom,” ask how many bathrooms are affected.
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
                        {"id": "bathroom_count_1", "title": "1 bathroom",   "description": ""},
                        {"id": "bathroom_count_2", "title": "2 bathrooms",  "description": ""},
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


# ─── 5) “Add Another Affected Area?” Button Prompt ───────────────────────

def send_add_area_confirmation_prompt(to: str, phone_number_id: str):
    """
    After any non‐countable area, ask: “Would you like to add another affected area?” (Yes/No).
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


# ─── 6) “Mold Growth Location” (List) ───────────────────────────────────

def send_mold_growth_location(to: str, phone_number_id: str):
    """
    After all areas are reported, ask “Where is the mold growth primarily located?”
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
    Summarizes everything so far, then prompts “Yes” / “No” to confirm the booking.
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
    1) Sends an internal “🚨 New Mold Enquiry Booking 🚨” alert to ALERT_NUMBERS.
    2) Prompts the user to upload wide-angle photos.
    3) Immediately follows with a single interactive list whose body reads:
       “While you wait, here’s our FAQ to learn more about our mold removal service:”
       so that it cannot be skipped.
    """
    state = get_user_state(MOLD_PREFIX, from_number) or {}
    if not state:
        return

    # Build the alert text that goes to internal numbers
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

    # 1) Send the alert to each internal admin number
    for admin in ALERT_NUMBERS:
        send_text_message(to=admin, body=alert_text)

    # 2) Prompt the user for photos with updated “Hang tight…” copy
    photo_prompt = (
        "Hang tight—we’re bringing in a real, live human support agent for you!\n"
        "They’ll join the chat as soon as they’re available.\n\n"
        "In the meantime, could you please take a wide-angle photo (from the door) "
        "capturing the full room or area affected? This helps us provide a rough estimate "
        "ahead of time. Just upload the images here in this chat. 😊"
    )
    send_text_message(to=from_number, body=photo_prompt)

    # 3) Immediately send the interactive FAQ list with “While you wait…” in its body
    send_mold_removal_faq_with_body_header(to=from_number)

    # We leave the user’s Redis state intact so that your live agent can pick up seamlessly.


# ─── 9) Main Flow Handler ────────────────────────────────────────────────

def handle_mold_flow(from_number: str, message: dict, user_state: dict):
    """
    Drives the entire mold-remediation flow. Uses user_state["step"] to decide how
    to interpret each incoming “text”, “button”, or “interactive” payload.
    """
    state = user_state or {}
    step = state.get("step", "")
    msg_type = message.get("type")  # “text”, “button”, or “interactive”

    # Helper: extract a quick‐reply button payload (id field)
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
                # Re-show the FAQ list (with the same “While you wait…” body) if they pick another question
                send_mold_removal_faq_with_body_header(to=from_number)
                return

    # ─── 2) BUTTONS (Quick-Reply) ───────────────────────────────────────
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_mold_flow: BUTTON payload='{payload_lower}'")

            # Refresh state after potential change
            state = get_user_state(MOLD_PREFIX, from_number) or {}
            step = state.get("step", "")

            # A) “Need help on Mold!”
            if payload_lower == "need help on mold!":
                clear_user_state(MOLD_PREFIX, from_number)
                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(MOLD_PREFIX, from_number, new_state)
                send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # B) step == “mold_option”
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
                    send_mold_removal_faq_with_body_header(to=from_number)
                    return

                if payload_lower == "return_main_menu":
                    clear_user_state(MOLD_PREFIX, from_number)
                    from flows.car_fumigation import send_main_menu
                    send_main_menu(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                # Fallback for an unrecognized button
                send_text_message(
                    to=from_number,
                    body="Sorry, I didn’t understand that. Type 'reset' to start over."
                )
                return

            # C) step == “mold_waiting_add_area_confirmation”
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

            # D) step == “mold_waiting_confirmation”
            if step == "mold_waiting_confirmation":
                if payload_lower == "mold_confirm_yes":
                    # 1) Internal alert      2) Photo prompt      3) FAQ list with body header
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

            # Fallback if `step` was something else
            send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
            return

    # ─── 3) LIST Replies (interactive.list_reply) ─────────────────────────
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_mold_flow: LIST payload='{selected_id}'")

        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        # A) step == “mold_select_area”
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

            # Otherwise (e.g. living, store, kitchen, furniture, etc.)
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) step == “mold_waiting_bedroom_count”
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

        # C) step == “mold_waiting_bathroom_count”
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

        # D) step == “mold_waiting_growth_location”
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
                state["step"] = ""  # Move on to summary
                set_user_state(MOLD_PREFIX, from_number, state)
                send_mold_removal_summary(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # Fallback if we couldn’t匹配 any known step
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── 4) Plain‐TEXT Handling ─────────────────────────────────────────────

    if msg_type == "text":
        text_body = message["text"]["body"].strip()
        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        print(f"[DEBUG] handle_mold_flow: TEXT at step='{step}' → '{text_body}'")

        # A) step == “mold_waiting_other_area”
        if step == "mold_waiting_other_area":
            state.setdefault("affected_areas", []).append("Other: " + text_body)
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) step == “mold_waiting_growth_other”
        if step == "mold_waiting_growth_other":
            state["growth_location"] = text_body
            state["step"] = ""  # Proceed to summary
            set_user_state(MOLD_PREFIX, from_number, state)
            send_mold_removal_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # Fallback for any other free‐text
        send_text_message(
            to=from_number,
            body="Sorry, I didn’t understand that. Type 'reset' to start over."
        )
        return

    # ─── 5) Fallback if no branch matched ─────────────────────────────────
    print(f"[DEBUG] handle_mold_flow: Unsupported msg_type='{msg_type}' or step='{step}'")
    send_text_message(
        to=from_number,
        body="Sorry, I can’t handle that type of message. Type 'reset' to start over."
    )
    return
