# flows/mold.py

import os
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_interactive_message
)

# ─── Module-Level Constants ──────────────────────────────────────────────────

PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Redis key prefix
MOLD_PREFIX = "mold"

# Internal alert recipients (without “+” prefix)
ALERT_NUMBERS = [
    "6587788080",  # Company: +65 8778 8080
    "6588662359",  # Bot:     +65 8866 2359
]

# All possible “affected area” options
MOLD_AREAS = [
    {"id": "area_bedroom",    "title": "Bedroom",       "description": "Mold in bedroom(s)"},
    {"id": "area_bathroom",   "title": "Bathroom",      "description": "Mold in bathroom(s)"},
    {"id": "area_store",      "title": "Store/Yard",    "description": "Store Room/Service Yard"},
    {"id": "area_living",     "title": "Living Area",   "description": "Mold in living/dining"},
    {"id": "area_kitchen",    "title": "Kitchen",       "description": "Mold in kitchen"},
    {"id": "area_furniture",  "title": "Furniture",     "description": "Mold on furniture"},
    {"id": "area_entire",     "title": "Entire Unit",   "description": "Whole unit affected"},
    {"id": "area_smell",      "title": "Mold Smell",    "description": "Odor detected"},
    {"id": "area_commercial", "title": "Commercial",    "description": "Office/shop affected"},
    {"id": "area_others",     "title": "Other Areas",   "description": "Unlisted areas"}
]

# Mapping of “growth_location” IDs → human-readable
GROWTH_CHOICES = {
    "growth_ceiling": "Ceiling only",
    "growth_walls":   "Walls only",
    "growth_both":    "Walls & ceiling",
    "growth_others":  None  # “Other” will be provided by user
}

# FAQ data: question ID → (title, answer text)
MOLD_FAQ_DATA = {
    "mfaq_safe": (
        "Is it safe for kids/pets?",
        "Yes, our mold removal and anti-mold painting treatments are safe for children and pets.\n\n"
        "We frequently service sensitive environments such as schools, laboratories, and hospitals. "
        "The anti-mold paint is odorless and low-VOC, ensuring minimal odor after completion."
    ),
    "mfaq_included": (
        "What’s included in your service?",
        "• Protection of flooring, furniture, and fittings to minimize post-service cleanup.\n"
        "• Chemical remediation: direct application, scrubbing, and removal of dead mold.\n"
        "• Complimentary removal of booklice if discovered (NEA-licensed Vector Operator).\n"
        "• Application of two coats of odorless, white anti-mold paint to prevent future mold growth."
    ),
    "mfaq_warranty": (
        "Do you provide a warranty?",
        "Yes. Our mold removal service comes with a 6- to 12-month warranty (depending on package).\n"
        "• Includes one complimentary inspection before expiry.\n"
        "• One-time complimentary mold removal if mold reappears within the warranty period.\n"
        "Note: The warranty does not cover mold caused by new, unresolved water leaks."
    ),
    "mfaq_preparation": (
        "How should I prepare?",
        "• Limit people in areas scheduled for treatment.\n"
        "• Remove loose items and personal belongings from treatment areas.\n"
        "• Remove curtains from windows in rooms scheduled for service.\n"
        "• Ensure access to ladders, fans, AC, or floor mats if needed.\n"
        "• Inform the technician if there are concealed areas (e.g., cabinets).\n"
        "• Relocate heavy or sensitive items that we cannot move safely.\n"
        "Note: We aim to arrive within 1 hour of the scheduled time; any delays will be communicated."
    ),
    "mfaq_duration": (
        "How long will it take?",
        "Typical durations:\n"
        "• Bedroom: 2–5 hours\n"
        "• Bathroom: 1–3 hours\n"
        "• Multiple areas: Technician advises after inspection.\n"
        "Actual time varies by drying, weather, and area size."
    ),
    "mfaq_payment": (
        "What payment options do you accept?",
        "• PayNow: UEN 201812722M\n"
        "• Atome: Interest-free installment (3 months) – 5% surcharge.\n"
        "• Cash: Please notify us in advance and prepare exact change."
    )
}


# ─── Helper Functions ───────────────────────────────────────────────────────

def build_list_payload(to: str, header_text: str, body_text: str, footer_text: str, button_label: str, sections: list):
    """
    Build a standard “interactive: list” payload. 
    `sections` should be a list of {"title": ..., "rows": [...] } blocks.
    """
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text",  "text": header_text},
            "body":   {"text": body_text},
            "footer": {"text": footer_text},
            "action": {
                "button":  button_label,
                "sections": sections
            }
        }
    }


def build_button_payload(to: str, body_text: str, buttons: list):
    """
    Build a standard “interactive: button” payload.
    `buttons` should be a list of {"id":..., "title":...} dicts.
    """
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": [{"type": "reply", "reply": b} for b in buttons]}
        }
    }


def get_interactive_id(msg: dict) -> str:
    """
    Extract a quick-reply / list-reply ID from an incoming message dict.
    Returns an empty string if none is found.
    """
    mtype = msg.get("type")
    if mtype == "button":
        return msg["button"].get("payload", "")
    if mtype == "interactive":
        itype = msg["interactive"].get("type", "")
        if itype == "button_reply":
            return msg["interactive"]["button_reply"].get("id", "")
        if itype == "list_reply":
            return msg["interactive"]["list_reply"].get("id", "")
    return ""


def send_unrecognized(to: str):
    """
    Send a uniform “unrecognized input” fallback message.
    """
    send_text_message(to, "Sorry, I didn’t understand that. Type 'reset' to start over.")


def send_internal_alert(user_phone: str, user_state: dict):
    """
    Build and send the “🚨 New Mold Enquiry Booking 🚨” alert to all ALERT_NUMBERS.
    """
    # Build lines of the summary
    lines = [
        "🚨 New Mold Enquiry Booking 🚨",
        "",
        f"Client Phone Number: +{user_phone}",
        "",
        "Affected Areas Reported:"
    ]
    for idx, area in enumerate(user_state.get("affected_areas", []), start=1):
        lines.append(f"{idx}.) {area}")

    if "bedroom_count" in user_state:
        lines.append(f"\nBedrooms affected: {user_state['bedroom_count']}")
    if "bathroom_count" in user_state:
        lines.append(f"Bathrooms affected: {user_state['bathroom_count']}")

    growth_id = user_state.get("growth_location")
    if growth_id:
        # If they chose “Others,” the actual text is stored in user_state["growth_location_text"]
        if growth_id == "growth_others":
            growth_text = user_state.get("growth_location_text", "")
        else:
            growth_text = GROWTH_CHOICES.get(growth_id, growth_id)
        lines.append(f"\nGrowth Location: {growth_text}")

    alert_body = "\n".join(lines)
    for admin in ALERT_NUMBERS:
        send_text_message(to=admin, body=alert_body)


def send_photo_prompt(to: str):
    """
    Prompts the user to upload a wide-angle photo, with the “Hang tight…” text.
    """
    text = (
        "Hang tight—we’re bringing in a real, live human support agent for you!\n"
        "They’ll join the chat as soon as they're available.\n\n"
        "In the meantime, could you please take a wide-angle photo (from the door) "
        "capturing the full room or area affected? This helps us provide a rough estimate ahead of time. "
        "Just upload the images here in this chat. 😊"
    )
    send_text_message(to, text)


def send_faq_list(to: str):
    """
    Send a brief “While you wait, here’s our FAQ…” header, then send the interactive FAQ list.
    """
    send_text_message(to, "While you wait, here’s our FAQ to learn more about our mold removal service:")
    # Build rows from MOLD_FAQ_DATA
    faq_rows = []
    for faq_id, (title, _) in MOLD_FAQ_DATA.items():
        faq_rows.append({"id": faq_id, "title": title, "description": ""})

    payload = build_list_payload(
        to=to,
        header_text="Mold Removal FAQ",
        body_text="Select a question to learn more:",
        footer_text="Tap a question",
        button_label="View FAQs",
        sections=[{"title": "FAQ Questions", "rows": faq_rows}]
    )
    send_interactive_message(payload)


# ─── 1) “Mold Option” Prompt ─────────────────────────────────────────────────

def send_mold_option_prompt(to: str):
    """
    Initial screen after the user taps “Need help on Mold!”:
    → [Request a Quotation]  [More Info on Service]  [Return to Main Menu]
    """
    buttons = [
        {"id": "mold_get_quote",  "title": "Request a Quotation"},
        {"id": "mold_more_info",  "title": "More Info on Service"},
        {"id": "return_main_menu", "title": "Return to Main Menu"}
    ]
    payload = build_button_payload(
        to=to,
        body_text="Welcome to Four Pest Solutions’ Mold Removal service!\n\nSelect an option below:",
        buttons=buttons
    )
    send_interactive_message(payload)

    state = {"step": "mold_option", "affected_areas": []}
    set_user_state(MOLD_PREFIX, to, state)


# ─── 2) “Select Affected Area” List ─────────────────────────────────────────

def go_to_area_selection(to: str):
    """
    Presents the list of mold-affected areas to choose one.
    """
    payload = build_list_payload(
        to=to,
        header_text="Mold Affected Areas",
        body_text="Please select an area affected by mold:",
        footer_text="Choose one",
        button_label="Select Area",
        sections=[{"title": "Affected Areas", "rows": MOLD_AREAS}]
    )
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_select_area"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 3) “Bedroom Count” List ─────────────────────────────────────────────────

def go_to_bedroom_count(to: str):
    """
    Asks “How many bedrooms are affected?”
    """
    rows = [
        {"id": "bedroom_count_1", "title": "1", "description": ""},
        {"id": "bedroom_count_2", "title": "2", "description": ""},
        {"id": "bedroom_count_3", "title": "3", "description": ""},
        {"id": "bedroom_count_4", "title": "4+", "description": ""}
    ]
    payload = build_list_payload(
        to=to,
        header_text="Number of Bedrooms Affected",
        body_text="How many bedrooms are affected?",
        footer_text="Select an option",
        button_label="Select Count",
        sections=[{"title": "Bedrooms Count", "rows": rows}]
    )
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bedroom_count"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 4) “Bathroom Count” List ────────────────────────────────────────────────

def go_to_bathroom_count(to: str):
    """
    Asks “How many bathrooms are affected?”
    """
    rows = [
        {"id": "bathroom_count_1", "title": "1", "description": ""},
        {"id": "bathroom_count_2", "title": "2", "description": ""},
        {"id": "bathroom_count_3", "title": "3", "description": ""},
        {"id": "bathroom_count_4", "title": "4+", "description": ""}
    ]
    payload = build_list_payload(
        to=to,
        header_text="Number of Bathrooms Affected",
        body_text="How many bathrooms are affected?",
        footer_text="Select an option",
        button_label="Select Count",
        sections=[{"title": "Bathrooms Count", "rows": rows}]
    )
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bathroom_count"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 5) “Add Another Affected Area?” Confirmation ────────────────────────────

def go_to_add_area_confirmation(to: str):
    """
    After choosing a non-countable area, ask:
    “Would you like to add another affected area?” (Yes/No)
    """
    buttons = [
        {"id": "add_area_yes", "title": "Yes"},
        {"id": "add_area_no",  "title": "No"}
    ]
    payload = build_button_payload(
        to=to,
        body_text="Would you like to add another affected area?",
        buttons=buttons
    )
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_add_area_confirmation"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 6) “Growth Location” List ──────────────────────────────────────────────

def go_to_growth_location(to: str):
    """
    Asks: “Where is the mold growth primarily located?”
    """
    rows = []
    for gid, label in GROWTH_CHOICES.items():
        # For “growth_others,” the label in GROWTH_CHOICES is None, so show “Others”
        title = label if label else "Others"
        rows.append({"id": gid, "title": title, "description": ""})

    payload = build_list_payload(
        to=to,
        header_text="Mold Growth Location",
        body_text="Where is the mold growth primarily located?",
        footer_text="Choose one",
        button_label="Select Location",
        sections=[{"title": "Growth Options", "rows": rows}]
    )
    send_interactive_message(payload)

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_growth_location"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 7) “Final Summary” & “Yes/No” Confirmation ──────────────────────────────

def go_to_summary(to: str):
    """
    Summarizes all collected fields, then prompts “Yes” or “No” to confirm the booking.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    data = state

    # Build a multi-line summary
    lines = ["Summary of your mold removal request:\n", "Affected Areas Reported:"]
    for idx, area in enumerate(data.get("affected_areas", []), start=1):
        lines.append(f"{idx}.) {area}")

    if "bedroom_count" in data:
        lines.append(f"\nBedrooms affected: {data['bedroom_count']}")
    if "bathroom_count" in data:
        lines.append(f"Bathrooms affected: {data['bathroom_count']}")

    growth_id = data.get("growth_location")
    if growth_id:
        if growth_id == "growth_others":
            growth_text = data.get("growth_location_text", "")
        else:
            growth_text = GROWTH_CHOICES.get(growth_id, growth_id)
        lines.append(f"\nGrowth Location: {growth_text}")

    summary_text = "\n".join(lines) + "\n\nSelect 'Yes' or 'No' to confirm."

    buttons = [
        {"id": "mold_confirm_yes", "title": "Yes"},
        {"id": "mold_confirm_no",  "title": "No"}
    ]
    payload = build_button_payload(to=to, body_text=summary_text, buttons=buttons)
    send_interactive_message(payload)

    state["step"] = "mold_waiting_confirmation"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 8) Main Flow Handler ────────────────────────────────────────────────────

def handle_mold_flow(from_number: str, message: dict, user_state: dict):
    """
    Central dispatcher for every incoming message after “Need help on Mold!” has been triggered.
    We inspect user_state["step"] and the payload (button vs. list vs. text) to decide next steps.
    """
    state = user_state or {}
    step = state.get("step", "")
    mtype = message.get("type")  # “text”, “button”, or “interactive”

    # Extract any quick-reply ID (button or list)
    payload_id = get_interactive_id(message)

    # ─── 1) If we’re on the FAQ screen (step == “mold_faq”) ───────────────────
    if step == "mold_faq":
        if payload_id.startswith("mfaq_"):
            # Show the chosen FAQ answer, then re-show the FAQ list
            _, answer_text = MOLD_FAQ_DATA.get(payload_id, ("", "Sorry, no info found."))
            send_text_message(to=from_number, body=answer_text)
            send_faq_list(to=from_number)
            return
        # If they send anything else, we fall through to “unrecognized”

    # ─── 2) Handling any quick-reply BUTTON (type == “button” or interactive button_reply) ─
    if mtype in ("button", "interactive") and payload_id:
        low = payload_id.lower()

        # ——— A) “Need help on Mold!” (starts the flow) ——————————————
        if low == "need help on mold!":
            clear_user_state(MOLD_PREFIX, from_number)
            send_mold_option_prompt(to=from_number)
            return

        # Refresh the current step from state
        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        # ——— B) If we’re on the “mold_option” screen ——————————————
        if step == "mold_option":
            if low == "mold_get_quote":
                # Start collecting “areas”
                state = {"step": "mold_select_area", "affected_areas": []}
                set_user_state(MOLD_PREFIX, from_number, state)
                go_to_area_selection(to=from_number)
                return

            if low == "mold_more_info":
                state["step"] = "mold_faq"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_faq_list(to=from_number)
                return

            if low == "return_main_menu":
                clear_user_state(MOLD_PREFIX, from_number)
                from flows.car_fumigation import send_main_menu
                send_main_menu(to=from_number, phone_number_id=PHONE_NUMBER_ID)
                return

            send_unrecognized(to=from_number)
            return

        # ——— C) If we’re waiting for “Add another area?” ——————————————
        if step == "mold_waiting_add_area_confirmation":
            if low == "add_area_yes":
                state["step"] = "mold_select_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                go_to_area_selection(to=from_number)
                return
            elif low == "add_area_no":
                state["step"] = "mold_prompt_growth"
                set_user_state(MOLD_PREFIX, from_number, state)
                go_to_growth_location(to=from_number)
                return
            else:
                send_text_message(to=from_number, body="Please select 'Yes' or 'No'.")
                return

        # ——— D) If we’re confirming the summary ——————————————
        if step == "mold_waiting_confirmation":
            if low == "mold_confirm_yes":
                # 1) Send internal alert
                send_internal_alert(user_phone=from_number, user_state=state)

                # 2) Clear user state (so nothing persists)
                clear_user_state(MOLD_PREFIX, from_number)

                # 3) Prompt them for photos
                send_photo_prompt(to=from_number)

                # 4) Attach the FAQ list
                send_faq_list(to=from_number)
                return

            if low == "mold_confirm_no":
                send_text_message(
                    to=from_number,
                    body="Let's update your mold details. Please select 'Request a Quotation' to restart."
                )
                clear_user_state(MOLD_PREFIX, from_number)
                return

            send_text_message(to=from_number, body="Please select 'Yes' or 'No'.")
            return

        # Any other button payload in an unexpected step:
        send_unrecognized(to=from_number)
        return

    # ─── 3) Handling LIST replies (type == "interactive" & interactive.type == "list_reply") ─
    if mtype == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        # ——— A) If we’re choosing an area ——————————————
        if step == "mold_select_area":
            # “Other Areas”?
            if selected_id == "area_others":
                state["step"] = "mold_waiting_other_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(to=from_number, body="Please specify the affected area not listed above:")
                return

            # Otherwise, add that area to the list
            chosen = next((a for a in MOLD_AREAS if a["id"] == selected_id), None)
            if chosen:
                state.setdefault("affected_areas", []).append(chosen["title"])

            # Now, choose next step:
            if selected_id == "area_bedroom":
                state["step"] = "mold_waiting_bedroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                go_to_bedroom_count(to=from_number)
                return

            if selected_id == "area_bathroom":
                state["step"] = "mold_waiting_bathroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                go_to_bathroom_count(to=from_number)
                return

            # Otherwise (like Living, Kitchen, Furniture, Entire, Smell, Commercial)
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            go_to_add_area_confirmation(to=from_number)
            return

        # ——— B) If we’re choosing bedroom count ——————————————
        if step == "mold_waiting_bedroom_count" and selected_id.startswith("bedroom_count_"):
            count = selected_id.split("_")[-1]
            state["bedroom_count"] = count
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            go_to_add_area_confirmation(to=from_number)
            return

        # ——— C) If we’re choosing bathroom count ——————————————
        if step == "mold_waiting_bathroom_count" and selected_id.startswith("bathroom_count_"):
            count = selected_id.split("_")[-1]
            state["bathroom_count"] = count
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            go_to_add_area_confirmation(to=from_number)
            return

        # ——— D) If we’re choosing growth location ——————————————
        if step == "mold_waiting_growth_location":
            if selected_id == "growth_others":
                # Ask for a custom entry
                state["step"] = "mold_waiting_growth_other"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(to=from_number, body="Please specify the mold growth location not listed above:")
                return
            else:
                # Normal growth choice (ceiling / walls / both)
                state["growth_location"] = selected_id
                set_user_state(MOLD_PREFIX, from_number, state)
                go_to_summary(to=from_number)
                return

        # Unrecognized list reply:
        send_unrecognized(to=from_number)
        return

    # ─── 4) Handling TEXT (free‐text) replies ───────────────────────────────────

    if mtype == "text":
        text = message["text"]["body"].strip()
        state = get_user_state(MOLD_PREFIX, from_number) or {}
        step = state.get("step", "")

        # ——— A) If we’re waiting for “Other Affected Area” text —————————
        if step == "mold_waiting_other_area":
            area_free = text
            state.setdefault("affected_areas", []).append(f"Other: {area_free}")
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            go_to_add_area_confirmation(to=from_number)
            return

        # ——— B) If we’re waiting for “Other Growth Location” text ————————
        if step == "mold_waiting_growth_other":
            state["growth_location"] = "growth_others"
            state["growth_location_text"] = text
            set_user_state(MOLD_PREFIX, from_number, state)
            go_to_summary(to=from_number)
            return

        # Otherwise, fallback
        send_unrecognized(to=from_number)
        return

    # ─── 5) Any other unsupported type ─────────────────────────────────────────
    send_text_message(to=from_number, body="Sorry, I can’t handle that type of message. Type 'reset' to start over.")
    return


# ─── 9) “Entry” Functions (exposed to dispatcher.py) ─────────────────────────

def send_mold_flow_entrypoint(to: str):
    """
    Called by dispatcher.py when the user taps “Need help on Mold!”
    (i.e. a button or text with payload “need help on mold!”).
    """
    clear_user_state(MOLD_PREFIX, to)
    send_mold_option_prompt(to=to)


def send_mold_option_prompt(to: str):
    """
    Exposed for dispatcher.py to call initially if needed
    (identical to section #1 above).
    """
    # This duplicates “send_mold_option_prompt” from above so we can
    # import it if dispatcher.py wants to call it directly.
    buttons = [
        {"id": "mold_get_quote",  "title": "Request a Quotation"},
        {"id": "mold_more_info",  "title": "More Info on Service"},
        {"id": "return_main_menu", "title": "Return to Main Menu"}
    ]
    payload = build_button_payload(
        to=to,
        body_text="Welcome to Four Pest Solutions’ Mold Removal service!\n\nSelect an option below:",
        buttons=buttons
    )
    send_interactive_message(payload)

    state = {"step": "mold_option", "affected_areas": []}
    set_user_state(MOLD_PREFIX, to, state)
