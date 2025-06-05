# flows/bedbug.py

import os
import time
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_template_message,
    send_list_message
)

# ─── Constants & Static Data ─────────────────────────────────────────────────
BEDBUG_PREFIX = "bedbug"   # Redis key prefix for Bedbug flow

# Pre-defined area options for Bedbug quoting:
BEDBUG_AREAS = [
    { "id": "bedbug_area_bed",       "title": "Bedroom(s)",        "description": "Where you sleep" },
    { "id": "bedbug_area_living",    "title": "Living Area",       "description": "Living room, sofas, etc." },
    { "id": "bedbug_area_whole",     "title": "Whole Unit",        "description": "Entire house/apartment" },
    { "id": "bedbug_area_commercial", "title": "Commercial Space", "description": "Office / Retail / Other" }
]

# Pre-set bedroom-count options:
BEDROOM_COUNT_ROWS = [
    { "id": "bedbug_count_1", "title": "1",  "description": "" },
    { "id": "bedbug_count_2", "title": "2",  "description": "" },
    { "id": "bedbug_count_3", "title": "3",  "description": "" },
    { "id": "bedbug_count_4", "title": "4",  "description": "" },
    { "id": "bedbug_count_5", "title": "5+", "description": "5 or more bedrooms" }
]


# ─── 1) send_bedbug_option_prompt ──────────────────────────────────────────────
def send_bedbug_option_prompt(to: str, phone_number_id: str):
    """
    Sends the initial Bedbug menu with three buttons:
      • Request a Quotation
      • More Info on Service
      • Return to Main Menu
    """
    text = (
        "We are happy to help with your bedbugs issue!\n\n"
        "Please select an option below for us to better understand what you are looking for."
    )

    # Build a “button”‐type interactive payload:
    interactive_payload = {
        "type": "button",
        "body": { "text": text },
        "action": {
            "buttons": [
                { "type": "reply", "reply": { "id": "bedbug_quote",      "title": "Request a Quotation"   } },
                { "type": "reply", "reply": { "id": "bedbug_more_info",   "title": "More Info on Service"  } },
                { "type": "reply", "reply": { "id": "bedbug_return_main", "title": "Return to Main Menu" } }
            ]
        }
    }

    # Instead of send_interactive_message(...), wrap it with send_text_message(...)
    resp = send_text_message({
        "to": to,                               # “to” must be plain digits (e.g. "6587788080")
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_bedbug_option_prompt → {resp}")


# ─── 2) send_bedbug_area_selection ──────────────────────────────────────────────
def send_bedbug_area_selection(to: str, phone_number_id: str):
    """
    Sends an interactive list of BEDBUG_AREAS (excluding ones already chosen).
    """
    state    = get_user_state(BEDBUG_PREFIX, to) or {}
    selected = state.get("affected_areas", [])

    # Filter out areas that are already in “affected_areas”
    available = [area for area in BEDBUG_AREAS if area["title"] not in selected]
    if not available:
        # If no more options remain, skip directly to bedroom‐count step
        _maybe_ask_bedroom_count(to, phone_number_id)
        return

    # Build “rows” for the list payload:
    rows = [
        { "id": item["id"], "title": item["title"], "description": item["description"] }
        for item in available
    ]

    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Select Affected Area(s)" },
        "body":   { "text": "Which area is affected by bedbugs? You may add multiple." },
        "footer": { "text": "Tap to choose" },
        "action": {
            "button": "Select Area",
            "sections": [
                { "title": "Possible Areas", "rows": rows }
            ]
        }
    }

    # Wrap list payload in send_text_message:
    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_bedbug_area_selection → {resp}")

    state["step"] = "bedbug_waiting_area_selection"
    set_user_state(BEDBUG_PREFIX, to, state)


# ─── 3) _maybe_ask_bedroom_count (helper) ─────────────────────────────────────────
def _maybe_ask_bedroom_count(to: str, phone_number_id: str):
    """
    If user has finished picking areas, move to bedroom‐count step.
    """
    state = get_user_state(BEDBUG_PREFIX, to) or {}
    # Mark that we’re waiting for bedroom count
    state["step"] = "bedbug_waiting_bedroom_count"
    set_user_state(BEDBUG_PREFIX, to, state)

    # Build a “list” payload of bedroom counts:
    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Number of Bedrooms Affected" },
        "body":   { "text": "How many bedrooms are affected?" },
        "footer": { "text": "Tap to choose" },
        "action": {
            "button": "Select Count",
            "sections": [
                { "title": "Bedrooms", "rows": BEDROOM_COUNT_ROWS }
            ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] _maybe_ask_bedroom_count → {resp}")


# ─── 4) send_bedbug_bedroom_count_prompt ─────────────────────────────────────────
def send_bedbug_bedroom_count_prompt(to: str, phone_number_id: str):
    """
    (If you want to force‐prompt for bedroom count directly, but our code
     calls _maybe_ask_bedroom_count above, so this may never actually fire.)
    """
    # In practice, we rarely call this directly—_maybe_ask_bedroom_count handles it.
    _maybe_ask_bedroom_count(to, phone_number_id)


# ─── 5) send_bedbug_area_add_confirmation_prompt ─────────────────────────────────
def send_bedbug_area_add_confirmation_prompt(to: str, phone_number_id: str):
    """
    After the user picks 1 area (or more), this asks “Would you like to add another area?”
    via Yes/No button interactive.
    """
    text = "Would you like to add another affected area?"

    interactive_payload = {
        "type": "button",
        "body": { "text": text },
        "action": {
            "buttons": [
                { "type": "reply", "reply": { "id": "bedbug_confirm_yes", "title": "Yes" } },
                { "type": "reply", "reply": { "id": "bedbug_confirm_no",  "title": "No"  } }
            ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_bedbug_area_add_confirmation_prompt → {resp}")

    state = get_user_state(BEDBUG_PREFIX, to) or {}
    state["step"] = "bedbug_waiting_area_add_confirmation"
    set_user_state(BEDBUG_PREFIX, to, state)


# ─── 6) send_bedbug_summary ─────────────────────────────────────────────────────
def send_bedbug_summary(to: str, phone_number_id: str):
    """
    Summarizes all collected bedbug details and asks for final confirmation.
    Shows a Yes/No interactive at the end.
    """
    state = get_user_state(BEDBUG_PREFIX, to) or {}
    data  = state

    # Build summary text
    areas         = data.get("affected_areas", [])
    bedroom_count = data.get("bedbug_bedroom_count", "Not provided")
    overall_count = data.get("bedbug_count", "Not provided")

    summary = "Bedbug Details Confirmation\n\n"
    summary += "Affected Area(s):\n"
    if areas:
        for idx, area in enumerate(areas, start=1):
            summary += f"{idx}. {area}\n"
    else:
        summary += "None\n"
    summary += f"\nNumber of Bedrooms Affected: {bedroom_count}\n"
    summary += f"Overall Bedbug Count Estimate: {overall_count}\n\n"
    summary += "Is this information correct?"

    interactive_payload = {
        "type": "button",
        "body": { "text": summary },
        "action": {
            "buttons": [
                { "type": "reply", "reply": { "id": "bedbug_confirm_yes", "title": "Yes" } },
                { "type": "reply", "reply": { "id": "bedbug_confirm_no",  "title": "No"  } }
            ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_bedbug_summary → {resp}")

    state["step"] = "bedbug_waiting_confirmation"
    set_user_state(BEDBUG_PREFIX, to, state)


# ─── 7) send_bedbug_faq_list ────────────────────────────────────────────────────
def send_bedbug_faq_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of Bedbug‐related FAQs.
    """
    faq_rows = [
        { "id": "bbfaq_safety",      "title": "Is it safe for kids & pets?",            "description": "" },
        { "id": "bbfaq_service_info", "title": "What does service include?",            "description": "" },
        { "id": "bbfaq_preparation", "title": "How to prepare before service?",          "description": "" },
        { "id": "bbfaq_duration",    "title": "How long will it take?",                 "description": "" },
        { "id": "bbfaq_warranty",    "title": "Warranty / Guarantee details",           "description": "" },
        { "id": "bbfaq_payment",     "title": "Payment methods & options",               "description": "" }
    ]

    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Bedbug FAQs" },
        "body":   { "text": "Select a question for more details:" },
        "footer": { "text": "Tap to choose" },
        "action": {
            "button": "Select FAQ",
            "sections": [
                { "title": "FAQ Topics", "rows": faq_rows }
            ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_bedbug_faq_list → {resp}")

    state = get_user_state(BEDBUG_PREFIX, to) or {}
    state["step"] = "bedbug_faq"
    set_user_state(BEDBUG_PREFIX, to, state)


# ─── 8) process_bedbug_faq_response ─────────────────────────────────────────────
def process_bedbug_faq_response(to: str, faq_id: str):
    """
    Sends back the selected FAQ answer as a plain text message.
    """
    faq_answers = {
        "bbfaq_safety": (
            "Yes—our bedbug treatments use NEA‐approved chemicals safe for families,\n"
            "and are carefully applied to avoid risk to pets or children."
        ),
        "bbfaq_service_info": (
            "Our bedbug service includes:\n"
            "• Comprehensive inspection\n"
            "• Heat treatment or chemical application (depending on infestation level)\n"
            "• Post‐treatment vacuuming and sealing\n"
            "• 30‐day warranty—re‐treatment if needed"
        ),
        "bbfaq_preparation": (
            "Before our team arrives:\n"
            "• Remove all bedding and linens\n"
            "• Vacuum carpets and floors\n"
            "• Clear clutter so we can access furniture\n"
            "• Keep pets/children away during treatment"
        ),
        "bbfaq_duration": (
            "Typical heat or chemical bedbug treatments take 3–5 hours,\n"
            "depending on square footage and infestation severity."
        ),
        "bbfaq_warranty": (
            "We provide a 30-day warranty on all bedbug treatments.\n"
            "If any bedbugs return, we will re-treat at no extra charge."
        ),
        "bbfaq_payment": (
            "We accept:\n"
            "• Cash on site\n"
            "• PayNow / PayLah!\n"
            "• Credit/Debit (Visa, Mastercard)\n"
            "• NETS"
        )
    }

    answer_text = faq_answers.get(faq_id, "Sorry, I could not find that FAQ.")
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": answer_text }
    })


# ─── 9) handle_bedbug_flow ──────────────────────────────────────────────────────
def handle_bedbug_flow(from_number: str, message: dict, api_key: str, base_url: str):
    """
    Main Bedbug flow dispatcher. ‘from_number’ is the full WhatsApp ID (e.g. "6587788080@c.us").
    """
    user_state = get_user_state(BEDBUG_PREFIX, from_number) or {}
    step = user_state.get("step", "")
    msg_type = message.get("type", "")

    # ─── A) “Reset” or “Need help on Bedbugs!” from main menu ───────────────────────
    if msg_type == "text" and message.get("body", "").strip().lower() == "reset":
        clear_user_state(BEDBUG_PREFIX, from_number)
        send_bedbug_option_prompt(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
        return

    if msg_type == "button" and message.get("body", "").strip().lower() == "need help on bedbugs!":
        clear_user_state(BEDBUG_PREFIX, from_number)
        send_bedbug_option_prompt(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
        return

    # ─── B) User tapped “Request a Quotation” / “More Info on Service” / “Return to Main Menu” ───
    if msg_type == "button" and step == "":
        payload = message.get("body", "").strip().lower()
        if payload == "bedbug_quote":
            # Begin quote: ask for first area
            new_state = { "step": "bedbug_select_area", "affected_areas": [] }
            set_user_state(BEDBUG_PREFIX, from_number, new_state)
            send_bedbug_area_selection(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
            return

        if payload == "bedbug_more_info":
            # Show FAQ list
            user_state["step"] = "bedbug_faq"
            set_user_state(BEDBUG_PREFIX, from_number, user_state)
            send_bedbug_faq_list(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
            return

        if payload == "bedbug_return_main":
            clear_user_state(BEDBUG_PREFIX, from_number)
            # Re-send main menu template:
            send_template_message(
                to=from_number.split("@")[0],
                template_name="main_menu_v2",
                template_params=["there"]
            )
            return

    # ─── C) User picked an “Affected Area” from the list ───────────────────────────
    if msg_type == "interactive" and step == "bedbug_select_area":
        choice_id = message.get("list_reply", {}).get("id", "")
        if choice_id:
            area_map = {
                "bedbug_area_bed":       "Bedroom(s)",
                "bedbug_area_living":    "Living Area",
                "bedbug_area_whole":     "Whole Unit",
                "bedbug_area_commercial": "Commercial Space"
            }
            selected_area = area_map.get(choice_id, "")
            if selected_area:
                state = user_state
                state.setdefault("affected_areas", []).append(selected_area)
                state["step"] = "bedbug_waiting_area_add_confirmation"
                set_user_state(BEDBUG_PREFIX, from_number, state)

                # Ask "Would you like to add another area?" 
                send_bedbug_area_add_confirmation_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

    # ─── D) User answered Yes/No to “add another area?” ───────────────────────────
    if msg_type == "button" and step == "bedbug_waiting_area_add_confirmation":
        payload = message.get("body", "").strip().lower()
        if payload == "bedbug_confirm_yes":
            # Ask for another area:
            state = user_state
            state["step"] = "bedbug_select_area"
            set_user_state(BEDBUG_PREFIX, from_number, state)
            send_bedbug_area_selection(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        if payload == "bedbug_confirm_no":
            # Move to bedroom count:
            _maybe_ask_bedroom_count(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
            return

    # ─── E) User picked “Number of Bedrooms Affected” ─────────────────────────────
    if msg_type == "interactive" and step == "bedbug_waiting_bedroom_count":
        bedroom_id = message.get("list_reply", {}).get("id", "")
        if bedroom_id:
            # Store bedroom count:
            state = user_state
            count_map = {
                "bedbug_count_1":  "1",
                "bedbug_count_2":  "2",
                "bedbug_count_3":  "3",
                "bedbug_count_4":  "4",
                "bedbug_count_5":  "5+"
            }
            state["bedbug_bedroom_count"] = count_map.get(bedroom_id, "Not provided")
            state["step"] = "bedbug_waiting_confirmation"
            set_user_state(BEDBUG_PREFIX, from_number, state)

            # After bedrooms, ask for overall estimate (free-text):
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {
                    "body": (
                        "Thanks! Please estimate how many bedbugs (approx.) you see in total. "
                        "For example: 10 – 20. You can type a range or a single number."
                    )
                }
            })
            return

    # ─── F) User provided “overall bedbug count estimate” ─────────────────────────
    if msg_type == "text" and step == "bedbug_waiting_confirmation":
        # Save the textual count estimate:
        estimate_text = message.get("body", "").strip()
        state = user_state
        state["bedbug_count"] = estimate_text
        state["step"] = "bedbug_confirm_summary"
        set_user_state(BEDBUG_PREFIX, from_number, state)

        # Show summary & confirmation (Yes/No):
        send_bedbug_summary(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
        return

    # ─── G) User confirmed the summary (Yes/No) ────────────────────────────────────
    if msg_type == "button" and step == "bedbug_confirm_summary":
        payload = message.get("body", "").strip().lower()
        if payload == "bedbug_confirm_yes":
            # Finalize appointment request. Clear state and send a thank-you message.
            data = user_state
            areas         = data.get("affected_areas", [])
            bedroom_count = data.get("bedbug_bedroom_count", "")
            overall_count = data.get("bedbug_count", "")

            clear_user_state(BEDBUG_PREFIX, from_number)
            confirmation = (
                "Thank you! Your bedbug request has been received.\n\n"
                f"Affected Areas: {', '.join(areas)}\n"
                f"Bedrooms Affected: {bedroom_count}\n"
                f"Bedbug Count Estimate: {overall_count}\n\n"
                "Our agent will contact you shortly. Meanwhile, you can view our Bedbug FAQ again:"
            )
            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": confirmation }
            })
            # Optionally re-show the FAQ
            send_bedbug_faq_list(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
            return

        if payload == "bedbug_confirm_no":
            # If user rejects summary, restart from picking areas:
            new_state = { "step": "bedbug_select_area", "affected_areas": [] }
            set_user_state(BEDBUG_PREFIX, from_number, new_state)
            send_bedbug_area_selection(to=from_number, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
            return

    # ─── H) User picked a FAQ row (interactive list) ─────────────────────────────
    if msg_type == "interactive" and step == "bedbug_faq":
        faq_id = message.get("list_reply", {}).get("id", "")
        if faq_id:
            process_bedbug_faq_response(to=from_number, faq_id=faq_id)
            return

    # ─── I) FALLBACK: nothing matched ─────────────────────────────────────────────
    clear_user_state(BEDBUG_PREFIX, from_number)
    send_text_message({
        "to": from_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Sorry, I can’t handle that type of message. Type 'reset' to start over." }
    })
