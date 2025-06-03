# flows/mold_remediation.py

import os
from datetime import datetime
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_interactive_message
)

# ─── Constants & Static Data ───

# Redis key prefix for Mold Remediation user states
MOLD_PREFIX = "mold"

# Mold‐area options (exactly as in your legacy list)
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


# ─── 1) FAQ Section ──────────────────────────────────────────────────────────

def send_mold_removal_faq(to: str, phone_number_id: str):
    """
    Sends an interactive FAQ list for Mold Removal.
    """
    payload = {
       "messaging_product": "whatsapp",
       "recipient_type": "individual",
       "to": to,
       "type": "interactive",
       "interactive": {
           "type": "list",
           "header": {"type": "text", "text": "Mold Removal FAQ"},
           "body": {"text": "Select a FAQ question:"},
           "footer": {"text": "Tap an option"},
           "action": {
               "button": "Select FAQ",
               "sections": [{
                   "title": "FAQ Questions",
                   "rows": [
                       {"id": "mfaq_safe",        "title": "Is it safe? Kids/Pets",   "description": "Are treatments safe for kids and pets?"},
                       {"id": "mfaq_included",    "title": "Service Details",          "description": "What's included in our service?"},
                       {"id": "mfaq_warranty",    "title": "Warranty Details",         "description": "Coverage and terms"},
                       {"id": "mfaq_preparation", "title": "Preparation",             "description": "How to prepare your space?"},
                       {"id": "mfaq_duration",    "title": "Service Duration",        "description": "How long does it take?"},
                       {"id": "mfaq_payment",     "title": "Payment Options",         "description": "Payment methods accepted"}
                   ]
               }]
           }
       }
    }
    send_interactive_message(payload)


def process_mold_faq_response(to: str, faq_id: str):
    """
    Sends back the appropriate FAQ answer as a simple text message.
    """
    faq_answers = {
       "mfaq_safe": (
           "Yes, our mold removal and anti-mold painting treatments are safe for children and pets.\n\n"
           "We frequently service sensitive environments such as schools, laboratories, and hospitals. "
           "The anti-mold paint we use is odorless, ensuring minimal odor after completion."
       ),
       "mfaq_included": (
           "Our mold removal service includes:\n\n"
           "• Protection of flooring, furniture, and fittings to minimize post-service cleanup.\n"
           "• Chemical remediation: direct application, scrubbing, and removal of dead mold.\n"
           "• Complimentary removal of booklice if discovered, as we are licensed by NEA as a Vector Operator in Singapore.\n"
           "• Application of two coats of odorless, white anti-mold paint to prevent future mold growth."
       ),
       "mfaq_warranty": (
           "We provide warranty coverage for all mold removal services to ensure lasting effectiveness. "
           "Warranty terms typically range from 6 to 12 months, depending on the service package and whether anti-mold painting is included.\n\n"
           "The warranty includes:\n"
           "• One complimentary inspection before warranty expiry (appointment required).\n"
           "• One-time complimentary mold removal during the warranty period if mold regrows.\n"
           "Note: Warranty does not cover mold regrowth due to external factors such as water leakage."
       ),
       "mfaq_preparation": (
           "To ensure a smooth service experience, please prepare the space by following these guidelines:\n"
           "• Limit the number of people in areas scheduled for treatment.\n"
           "• Remove loose items and personal belongings from treatment areas.\n"
           "• Remove curtains from windows in rooms scheduled for service.\n"
           "• Ensure access to equipment (ladders, fans, AC, floor mats) if needed.\n"
           "• Inform our technician on the day if there are concealed areas (e.g., cabinets).\n"
           "• Relocate heavy or sensitive items, as we may not be able to move them safely.\n"
           "Please note: We aim to arrive within 1 hour of the scheduled time; any delays will be communicated."
       ),
       "mfaq_duration": (
           "Typical service durations are as follows:\n"
           "• Bedroom: Approximately 2 to 5 hours\n"
           "• Bathroom: Approximately 1 to 3 hours\n"
           "• Multiple areas: Our technician will advise duration upon inspection\n"
           "Note: Duration may vary based on drying times, weather, and the size of the area."
       ),
       "mfaq_payment": (
           "We accept the following payment methods:\n"
           "• PayNow: Payment via UEN: 201812722M\n"
           "• Atome: Interest-free installment for 3 months (a 5% surcharge applies)\n"
           "• Cash: Please inform us in advance if you need to pay in cash and prepare the exact amount."
       )
    }

    answer = faq_answers.get(faq_id, "Sorry, no information is available for that question.")
    send_text_message(to, answer)


# ─── 2) “Request a Quotation” / Option Prompt ─────────────────────────────────

def send_mold_option_prompt(to: str, phone_number_id: str):
    """
    Sends the initial “Mold Remediation” options: Request a Quotation, More Info, or Return to Main Menu.
    """
    text = "We are happy to help! Select an option below for us to better understand what you are looking for!"
    payload = {
       "messaging_product": "whatsapp",
       "recipient_type": "individual",
       "to": to,
       "type": "interactive",
       "interactive": {
           "type": "button",
           "body": {"text": text},
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


# ─── 3) “Select Mold Area” → Interactive List ─────────────────────────────────

def send_mold_area_selection(to: str, phone_number_id: str):
    """
    Step: List out all MOLD_AREAS as a WhatsApp interactive list. 1 entry at a time.
    """
    # Fetch existing selected areas (if any) so we don’t resend them
    state = get_user_state(MOLD_PREFIX, to) or {}
    selected = state.get("affected_areas", [])

    # Filter out already‐selected area titles
    available = [area for area in MOLD_AREAS if area["title"] not in selected]
    if not available:
        # If nothing left to choose, move to growth location
        send_mold_growth_location(to, phone_number_id)
        return

    rows = [{"id": area["id"], "title": area["title"], "description": area["description"]} for area in available]
    payload = {
       "messaging_product": "whatsapp",
       "recipient_type": "individual",
       "to": to,
       "type": "interactive",
       "interactive": {
           "type": "list",
           "header": {"type": "text", "text": "Mold Affected Areas"},
           "body": {"text": "Select 1 or multiple areas affected by mold (1 entry at a time):"},
           "footer": {"text": "Select Area"},
           "action": {
               "button": "Select Area",
               "sections": [{"title": "Affected Areas", "rows": rows}]
           }
       }
    }
    send_interactive_message(payload)

    # Mark in Redis that we’re awaiting a list reply for the area selection
    state["step"] = "mold_waiting_area_selection"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 4) Bedroom / Bathroom Count Prompts ──────────────────────────────────────

def send_bedroom_count_prompt(to: str, phone_number_id: str):
    """
    After the user picks “Bedroom,” ask how many bedrooms are affected.
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
                   "title": "Bedroom Count",
                   "rows": [
                       {"id": "bedroom_count_1", "title": "1 bedroom",                 "description": "One bedroom affected"},
                       {"id": "bedroom_count_2", "title": "2 bedrooms",                "description": "Two bedrooms affected"},
                       {"id": "bedroom_count_3", "title": "3 bedrooms or more",        "description": "Three or more"}
                   ]
               }]
           }
       }
    }
    send_interactive_message(payload)

    # Mark that we’re awaiting bedroom count
    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bedroom_count"
    set_user_state(MOLD_PREFIX, to, state)


def send_bathroom_count_prompt(to: str, phone_number_id: str):
    """
    After the user picks “Bathroom,” ask how many bathrooms are affected.
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
                   "title": "Bathroom Count",
                   "rows": [
                       {"id": "bathroom_count_1", "title": "1 bathroom",                 "description": "One bathroom affected"},
                       {"id": "bathroom_count_2", "title": "2 bathrooms",                "description": "Two bathrooms affected"},
                       {"id": "bathroom_count_3", "title": "3 bathrooms or more",        "description": "Three or more"}
                   ]
               }]
           }
       }
    }
    send_interactive_message(payload)

    # Mark that we’re awaiting bathroom count
    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bathroom_count"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 5) Confirmation of “Add Another Area?” ───────────────────────────────────

def send_add_area_confirmation_prompt(to: str, phone_number_id: str):
    """
    After any area selection (other than bedroom/bathroom), ask:
    “Would you like to add another affected area?”
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


# ─── 6) Growth Location Prompt ────────────────────────────────────────────────

def send_mold_growth_location(to: str, phone_number_id: str):
    """
    Asks: “Where did you spot the mold growth?” with a list of options.
    """
    payload = {
       "messaging_product": "whatsapp",
       "recipient_type": "individual",
       "to": to,
       "type": "interactive",
       "interactive": {
           "type": "list",
           "header": {"type": "text", "text": "Mold Growth Location"},
           "body": {"text": "Where did you spot the mold growth?\nSelect one:"},
           "footer": {"text": "Choose an option"},
           "action": {
               "button": "Select Location",
               "sections": [{
                   "title": "Growth Options",
                   "rows": [
                       {"id": "growth_ceiling", "title": "Ceiling only",       "description": "Mold on ceiling"},
                       {"id": "growth_walls",   "title": "Walls only",         "description": "Mold on walls"},
                       {"id": "growth_both",    "title": "Walls and ceiling",  "description": "Mold on both"},
                       {"id": "growth_others",  "title": "Others",             "description": "Enter custom location"}
                   ]
               }]
           }
       }
    }
    send_interactive_message(payload)
    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_growth_location"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 7) Summary & Confirmation ───────────────────────────────────────────────

def send_mold_removal_summary(to: str, phone_number_id: str):
    """
    Summarizes all data collected so far, then asks “Yes”/“No” to confirm.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    data = state

    # Build a textual summary
    summary = "Summary of your mold removal request:\n\nAffected Areas Reported:\n"
    selected_areas = data.get("affected_areas", [])
    for idx, area in enumerate(selected_areas, start=1):
        summary += f"{idx}.) {area}\n"

    if "bedroom_count" in data:
        summary += f"\nBedrooms affected: {data['bedroom_count']}\n"
    if "bathroom_count" in data:
        summary += f"Bathrooms affected: {data['bathroom_count']}\n"
    if "growth_location" in data:
        # Map the choice to human‐readable text if it’s a known ID
        growth_map = {
            "growth_ceiling": "Ceiling only",
            "growth_walls":   "Walls only",
            "growth_both":    "Walls and ceiling"
        }
        chosen = growth_map.get(data["growth_location"], data["growth_location"])
        summary += f"\nGrowth Location: {chosen}\n"

    body_text = summary + "\nSelect 'Yes' or 'No' to confirm."
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


# ─── 8) Main Flow‐Handler: handle_mold_flow ────────────────────────────────────

def handle_mold_flow(from_number: str, message: dict, user_state: dict):
    """
    This single function drives the entire Mold Remediation flow, similar to handle_car_fumigation_flow.
    We look at user_state["step"], extract either a button‐payload or list‐reply User ID, or plain‐text, and advance the flow.
    """
    state = user_state or {}
    step = state.get("step", "")
    msg_type = message.get("type")  # "text", "button", or "interactive"

    # ── Helper to extract a quick‐reply button ID ────────────────────────────────
    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"]["payload"]
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"]["id"]
        return ""

    # ─── 1) FAQ Handling (if step == "mold_faq") ─────────────────────────────────
    if step == "mold_faq":
        # A) Button‐reply under “FAQ”
        if msg_type in ["button", "interactive"]:
            payload = extract_button_payload(message)
            if payload and payload.startswith("mfaq_"):
                process_mold_faq_response(from_number, payload)
                # Re‐show FAQ list so user can pick another question
                send_mold_removal_faq(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

    # ─── 2) Handle quick‐reply BUTTONS (“button” or “interactive.button_reply”) ──
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            # print debug
            print(f"[DEBUG] handle_mold_flow: BUTTON payload='{payload_lower}' from {from_number}")
            state = user_state or {}
            step = state.get("step", "")

            # A) “Need help on Mold!” from main menu → start mold flow
            if payload_lower == "need help on mold!":
                clear_user_state(MOLD_PREFIX, from_number)
                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(MOLD_PREFIX, from_number, new_state)
                send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # B) On the Mold‐option screen:
            if step == "mold_option":
                # “Request a Quotation”
                if payload_lower == "mold_get_quote":
                    # Initialize state and jump to area selection
                    state = {"step": "mold_select_area", "affected_areas": []}
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_area_selection(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                # “More Info on Service” → show FAQ
                if payload_lower == "mold_more_info":
                    state["step"] = "mold_faq"
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_removal_faq(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                # “Return to Main Menu”
                if payload_lower == "return_main_menu":
                    clear_user_state(MOLD_PREFIX, from_number)
                    from flows.car_fumigation import send_main_menu
                    send_main_menu(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                # If none matched, fallback
                send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
                return

            # C) “Add Another Area?” step
            if step == "mold_waiting_add_area_confirmation":
                if payload_lower == "add_area_yes":
                    state.pop("step", None)
                    state["step"] = "mold_select_area"
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_area_selection(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return
                elif payload_lower == "add_area_no":
                    state.pop("step", None)
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

            # D) “Entire Unit Inspection?” step is not used in your current logic (only for area_entire branch),
            #    so we will skip it (or eventually we can integrate similarly).

            # E) “Summary Confirmation” step:
            if step == "mold_waiting_confirmation":
                if payload_lower == "mold_confirm_yes":
                    send_text_message(
                        to=from_number,
                        body=(
                            "Hold on tight—we’re summoning a real, living, breathing, functioning human support agent for you! "
                            "They’ll join this chat as soon as they're available. In the meantime, feel free to explore our other services and read our FAQ!"
                        )
                    )
                    clear_user_state(MOLD_PREFIX, from_number)
                    return

                elif payload_lower == "mold_confirm_no":
                    send_text_message(to=from_number, body="Let's update your mold details. Please select 'Request a Quotation' to restart.")
                    clear_user_state(MOLD_PREFIX, from_number)
                    return

                else:
                    send_text_message(to=from_number, body="Please select 'Yes' or 'No'.")
                    return

            # F) Fallback
            send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
            return

    # ─── 3) Handle interactive LIST replies ──────────────────────────────────────
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_mold_flow: LIST payload='{selected_id}' from {from_number}")

        state = user_state or {}
        step = state.get("step", "")

        # A) If we just chose an area:
        if step == "mold_select_area":
            # “Other Areas”?
            if selected_id == "area_others":
                state["step"] = "mold_waiting_other_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(to=from_number, body="Please specify the affected area not listed above:")
                return

            # Normal area selection
            area_obj = next((a for a in MOLD_AREAS if a["id"] == selected_id), None)
            if area_obj:
                chosen_title = area_obj["title"]
                # Append that area to Redis state
                state.setdefault("affected_areas", []).append(chosen_title)

            # Now remove the “awaiting_area_selection” flag
            state.pop("step", None)

            # If user chose “Bedroom”
            if selected_id == "area_bedroom":
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bedroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # If user chose “Bathroom”
            if selected_id == "area_bathroom":
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bathroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # Otherwise, ask “Add another area?”
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) If we’re waiting for bedroom count:
        if step == "mold_waiting_bedroom_count":
            # e.g. “bedroom_count_2”
            if selected_id.startswith("bedroom_count_"):
                count = selected_id.split("_")[-1]
                state["bedroom_count"] = count
                state.pop("step", None)
                set_user_state(MOLD_PREFIX, from_number, state)
                send_add_area_confirmation_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # C) If we’re waiting for bathroom count:
        if step == "mold_waiting_bathroom_count":
            if selected_id.startswith("bathroom_count_"):
                count = selected_id.split("_")[-1]
                state["bathroom_count"] = count
                state.pop("step", None)
                set_user_state(MOLD_PREFIX, from_number, state)
                send_add_area_confirmation_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # D) If we’re waiting for growth location:
        if step == "mold_waiting_growth_location":
            if selected_id == "growth_others":
                state["step"] = "mold_waiting_growth_other"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(to=from_number, body="Please specify the mold growth location not listed above:")
                return
            else:
                # A normal growth location (e.g. "growth_walls")
                state["growth_location"] = selected_id
                state.pop("step", None)
                set_user_state(MOLD_PREFIX, from_number, state)
                send_mold_removal_summary(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # Otherwise, fallback
        send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
        return

    # ─── 4) Handle plain‐TEXT replies at “collect_*” steps ────────────────────────
    if msg_type == "text":
        text_body = message["text"]["body"].strip()
        state = user_state or {}
        step = state.get("step", "")

        print(f"[DEBUG] handle_mold_flow: TEXT at step='{step}' → '{text_body}' from {from_number}")

        # A) If we asked for “Other Area” text
        if step == "mold_waiting_other_area":
            # Append “Other: <whatever they typed>”
            state.setdefault("affected_areas", []).append("Other: " + text_body)
            state.pop("step", None)
            set_user_state(MOLD_PREFIX, from_number, state)

            # Then ask “Add another area?”
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) If we asked for “Other Growth Location” text
        if step == "mold_waiting_growth_other":
            state["growth_location"] = text_body
            state.pop("step", None)
            set_user_state(MOLD_PREFIX, from_number, state)

            # Now show the final summary
            send_mold_removal_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # C) Any other text outside an expected step
        send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
        return

    # ─── 5) Fallback (unsupported payload) ──────────────────────────────────────
    print(f"[DEBUG] handle_mold_flow: Unsupported msg_type='{msg_type}'")
    send_text_message(to=from_number, body="Sorry, I can’t handle that type of message. Type 'reset' to start over.")
    return
