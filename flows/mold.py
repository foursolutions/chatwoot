# flows/mold.py

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

# List of possible affected areas with IDs, titles, and descriptions
MOLD_AREAS = [
    {"id": "area_bedroom", "title": "Bedroom", "description": "Bedrooms affected"},
    {"id": "area_bathroom", "title": "Bathroom", "description": "Bathrooms affected"},
    {"id": "area_living", "title": "Living Room", "description": "Living area affected"},
    {"id": "area_kitchen", "title": "Kitchen", "description": "Kitchen area affected"},
    {"id": "area_others", "title": "Other", "description": "Other areas not listed above"}
]

# Mapping for FAQ questions and their responses
MOLD_FAQ = {
    "mfaq_safe": "Is mold removal safe? Yes—our chemicals are EPA-approved and safe for homes with kids/pets.",
    "mfaq_included": "What’s included in mold removal? We perform inspection, chemical application, scrubbing, and post-treatment wipe down.",
    "mfaq_warranty": "Do you provide a warranty? Yes, 1-year limited warranty on treated surfaces.",
    "mfaq_preparation": "How should I prepare? Remove personal items, clear affected surfaces, and ensure good ventilation.",
    "mfaq_duration": "How long will it take? Most residential jobs take 2–4 hours depending on severity.",
    "mfaq_payment": "What are the payment options? We accept PayNow, bank transfer, and cash upon completion."
}


# ─── 1) Top‐Level “Mold Options” Prompt ─────────────────────────────────────────
def send_mold_option_prompt(to: str, phone_number_id: str):
    """
    Show buttons: [Request a Quotation], [More Info on Service], [Return to Main Menu]
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "We are happy to help! Select an option below for us to better understand what you are looking for!"},
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


# ─── 2) “Affected Areas” List Prompt ────────────────────────────────────────────
def send_mold_area_selection(to: str, phone_number_id: str):
    """
    Step: List out all MOLD_AREAS as a WhatsApp interactive list.
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
            "body": {"text": "Please select an area affected by mold:"},
            "footer": {"text": "Choose one"},
            "action": {
                "button": "Select Area",
                "sections": [{"title": "Affected Areas", "rows": rows}]
            }
        }
    }
    send_interactive_message(payload)

    # We already set "step" to "mold_select_area" before calling this function,
    # so do not overwrite it here. Once user taps an area, handle_mold_flow will catch it.


# ─── 3) “Other Areas” Confirmation Prompt ────────────────────────────────────────
def send_add_area_confirmation_prompt(to: str, phone_number_id: str):
    """
    After each area is chosen (or “Other” text entered), ask if the user wants to add more.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Would you like to report another affected area?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "add_area_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "add_area_no", "title": "No"}}
                ]
            }
        }
    }
    send_interactive_message(payload)


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
                   "title": "Bedrooms",
                   "rows": [
                       {"id": "bedroom_count_1", "title": "1", "description": ""},
                       {"id": "bedroom_count_2", "title": "2", "description": ""},
                       {"id": "bedroom_count_3", "title": "3+", "description": ""}
                   ]
               }]
           }
       }
    }
    send_interactive_message(payload)


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
                   "title": "Bathrooms",
                   "rows": [
                       {"id": "bathroom_count_1", "title": "1", "description": ""},
                       {"id": "bathroom_count_2", "title": "2", "description": ""},
                       {"id": "bathroom_count_3", "title": "3+", "description": ""}
                   ]
               }]
           }
       }
    }
    send_interactive_message(payload)


# ─── 5) “Mold Growth Location” Prompt ──────────────────────────────────────────
def send_mold_growth_location(to: str, phone_number_id: str):
    """
    After all areas have been selected, ask where mold growth is located (Walls, Ceiling, Both, or Other).
    """
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
                "button": "Select Growth Location",
                "sections": [{
                    "title": "Growth Options",
                    "rows": [
                        {"id": "growth_walls", "title": "Walls Only", "description": ""},
                        {"id": "growth_ceiling", "title": "Ceiling Only", "description": ""},
                        {"id": "growth_both", "title": "Walls & Ceiling", "description": ""},
                        {"id": "growth_others", "title": "Other", "description": ""}
                    ]
                }]
            }
        }
    }
    send_interactive_message(payload)

    # Mark that we’re awaiting growth location selection
    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_growth_location"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 6) “Mold Removal Summary” ─────────────────────────────────────────────────
def send_mold_removal_summary(to: str, phone_number_id: str):
    """
    Summarize the user’s inputs (areas, counts, growth location) and ask for confirmation.
    """
    state = get_user_state(MOLD_PREFIX, to)
    if not state:
        # If somehow state is missing, restart
        send_text_message(to=to, body="Oops, something went wrong. Please type 'need help on mold!' to try again.")
        return

    summary = "Summary of your mold removal request:\n\nAffected Areas Reported:\n"
    for idx, area in enumerate(state.get("affected_areas", []), start=1):
        summary += f"{idx}.) {area}\n"

    if "bedroom_count" in state:
        summary += f"\nBedrooms affected: {state['bedroom_count']}\n"
    if "bathroom_count" in state:
        summary += f"\nBathrooms affected: {state['bathroom_count']}\n"

    if "growth_location" in state:
        growth_map = {
            "growth_ceiling": "Ceiling only",
            "growth_walls": "Walls only",
            "growth_both": "Walls and ceiling"
        }
        chosen = growth_map.get(state["growth_location"], state["growth_location"])
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
                    {"type": "reply", "reply": {"id": "mold_confirm_no", "title": "No"}}
                ]
            }
        }
    }
    send_interactive_message(payload)

    # Mark that we’re awaiting final confirmation
    state["step"] = "mold_waiting_confirmation"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 7) Mold Removal FAQ List ───────────────────────────────────────────────────
def send_mold_removal_faq(to: str, phone_number_id: str):
    """
    Send an interactive list of FAQ questions related to mold removal.
    """
    rows = [
        {"id": "mfaq_safe", "title": "Is it safe? Kids/Pets", "description": ""},
        {"id": "mfaq_included", "title": "What’s included?", "description": ""},
        {"id": "mfaq_warranty", "title": "Do you provide a warranty?", "description": ""},
        {"id": "mfaq_preparation", "title": "How to prepare?", "description": ""},
        {"id": "mfaq_duration", "title": "How long will it take?", "description": ""},
        {"id": "mfaq_payment", "title": "Payment options", "description": ""}
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
                "sections": [{"title": "FAQ", "rows": rows}]
            }
        }
    }
    send_interactive_message(payload)

    # Redis state should remain "mold_faq" so that we catch list replies
    # in handle_mold_flow (no need to reset step here).


def process_mold_faq_response(to: str, faq_id: str):
    """
    Given a selected FAQ ID, send the corresponding answer text.
    """
    answer = MOLD_FAQ.get(faq_id, "Sorry, I don't have information on that.")
    send_text_message(to=to, body=answer)


# ─── 8) Main Flow Handler ──────────────────────────────────────────────────────
def handle_mold_flow(from_number: str, message: dict, user_state: dict):
    """
    Drives the entire Mold Remediation flow. Uses user_state["step"] to route
    list‐replies, button quick‐replies, and plain text through each stage.
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

        # B) If user tapped a row in the FAQ LIST
        if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
            selected_id = message["interactive"]["list_reply"]["id"]
            if selected_id.startswith("mfaq_"):
                process_mold_faq_response(from_number, selected_id)
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

            # ───────── A) Return to Main Menu ─────────────────────────────────────
            if payload_lower == "return_main_menu":
                # Clear mold state and show car fumigation main menu
                clear_user_state(MOLD_PREFIX, from_number)
                from flows.car_fumigation import send_main_menu
                send_main_menu(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
                return

            # ───────── B) Back to Mold‐Option Screen ───────────────────────────────
            if payload_lower == "mold_back":
                new_state = {"step": "mold_option", "affected_areas": []}
                set_user_state(MOLD_PREFIX, from_number, new_state)
                send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # ───────── C) On the Mold‐option screen ────────────────────────────────
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

                # “More Info on Service”
                if payload_lower == "mold_more_info":
                    state["step"] = "mold_faq"
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_removal_faq(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

            # ───────── D) A “Yes/No” to add another area ────────────────────────────
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

            # ───────── E) Final Confirmation (“Yes” / “No”) ─────────────────────────
            if step == "mold_waiting_confirmation":
                if payload_lower == "mold_confirm_yes":
                    send_text_message(to=from_number, body="Hold on tight—we’re summoning a real human agent to finalize your mold removal request!")
                    clear_user_state(MOLD_PREFIX, from_number)
                    return
                elif payload_lower == "mold_confirm_no":
                    send_text_message(to=from_number, body="Let's update your mold details. Please select 'Request a Quotation' to restart.")
                    clear_user_state(MOLD_PREFIX, from_number)
                    return

    # ─── 3) LIST reply handling (e.g., area selection, bedroom/bathroom count, growth location) ───
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        selected_id = message["interactive"]["list_reply"]["id"]
        state = state or {}
        step = state.get("step", "")

        # A) Area selection (step == "mold_select_area")
        if step == "mold_select_area":
            if selected_id == "area_others":
                state["step"] = "mold_waiting_other_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(to=from_number, body="Please specify the affected area not listed above:")
                return
            else:
                area_obj = next((a for a in MOLD_AREAS if a["id"] == selected_id), None)
                if area_obj:
                    chosen_title = area_obj["title"]
                    state.setdefault("affected_areas", []).append(chosen_title)

                # Now ask if user wants to add another area
                state["step"] = "mold_waiting_add_area_confirmation"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_add_area_confirmation_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

        # B) Bedroom count (step == "mold_waiting_bedroom_count")
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

        # C) Bathroom count (step == "mold_waiting_bathroom_count")
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

        # D) Growth location (step == "mold_waiting_growth_location")
        if step == "mold_waiting_growth_location":
            if selected_id == "growth_others":
                state["step"] = "mold_waiting_growth_other"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_text_message(to=from_number, body="Please specify the mold growth location not listed above:")
                return
            else:
                state["growth_location"] = selected_id
                state.pop("step", None)
                set_user_state(MOLD_PREFIX, from_number, state)
                send_mold_removal_summary(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

    # ─── 4) Plain text handling (e.g., “Other” inputs for area or growth) ─────────
    if msg_type == "text":
        text_body = message["text"]["body"].strip()
        state = state or {}
        step = state.get("step", "")

        # A) If we asked for “Other Area” text
        if step == "mold_waiting_other_area":
            state.setdefault("affected_areas", []).append("Other: " + text_body)
            # Now ask if user wants to add another area
            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
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
            send_mold_removal_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # C) Any other text outside an expected step
        send_text_message(to=from_number, body="Sorry, I didn’t understand that. Type 'reset' to start over.")
        return

    # ─── 5) Fallback (unsupported payload) ──────────────────────────────────────
    print(f"[DEBUG] handle_mold_flow: Unsupported msg_type='{msg_type}' or step='{step}'")
    send_text_message(to=from_number, body="Sorry, I can’t handle that type of message. Type 'reset' to start over.")
    return
