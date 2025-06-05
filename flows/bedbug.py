# flows/bedbug.py

import os
import time
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_interactive_message
)

# ─── Constants & Static Data ─────────────────────────────────────────────────

BEDBUG_PREFIX = "bedbug"   # Redis key prefix for Bedbug flow

# Interactive list of areas a user can select when reporting bedbugs
BEDBUG_AREAS = [
    { "id": "bedbug_area_bed",        "title": "Bedroom(s)",       "description": "Bedbugs in bedroom(s)"        },
    { "id": "bedbug_area_living",     "title": "Living Area",      "description": "Bedbugs in living area"       },
    { "id": "bedbug_area_whole",      "title": "Whole Unit",       "description": "Bedbugs all over the unit"    },
    { "id": "bedbug_area_commercial", "title": "Commercial Space", "description": "Bedbugs in commercial space"   },
    { "id": "bedbug_area_others",     "title": "Others",           "description": "Other areas (specify)"         }
]

# ─── 1) Initial Bedbug‐Option Prompt ──────────────────────────────────────────
def send_bedbug_option_prompt(to: str, phone_number_id: str):
    """
    Sends the initial Bedbug menu with three buttons:
      • Request a Quotation
      • More Info on Service
      • Return to Main Menu
    """
    text = "We are happy to help with your bedbugs issue! Select an option below for us to better understand what you are looking for!"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": { "text": text },
            "action": {
                "buttons": [
                    { "type": "reply", "reply": { "id": "bedbug_quote",     "title": "Request a Quotation" } },
                    { "type": "reply", "reply": { "id": "bedbug_more_info", "title": "More Info on Service" } },
                    { "type": "reply", "reply": { "id": "return_main_menu", "title": "Return to Main Menu" } }
                ]
            }
        }
    }
    send_interactive_message(payload)

    # Set current step in Redis
    state = { "step": "bedbug_option", "affected_areas": [] }
    set_user_state(BEDBUG_PREFIX, to, state)

# ─── 2) Affected‐Area Selection (Interactive List) ────────────────────────────
def send_bedbug_area_selection(to: str, phone_number_id: str):
    """
    Sends an interactive list of BEDBUG_AREAS (excluding ones already chosen).
    """
    state    = get_user_state(BEDBUG_PREFIX, to) or {}
    selected = state.get("affected_areas", [])

    # Filter out areas that are already in “affected_areas”
    available = [area for area in BEDBUG_AREAS if area["title"] not in selected]
    if not available:
        # If no more options, skip directly to count prompts
        _maybe_ask_bedroom_count(to, phone_number_id)
        return

    rows = [
        { "id": area["id"], "title": area["title"], "description": area["description"] }
        for area in available
    ]
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Bedbug Affected Areas" },
            "body":   { "text": "Select 1 or multiple areas affected by bedbugs (1 entry at a time):" },
            "footer": { "text": "Select Area" },
            "action": {
                "button": "Select Area",
                "sections": [ { "title": "Affected Areas", "rows": rows } ]
            }
        }
    }
    send_interactive_message(payload)

    state["step"] = "bedbug_waiting_area_selection"
    set_user_state(BEDBUG_PREFIX, to, state)

# ─── 3) Bedroom Count Prompt ──────────────────────────────────────────────────
def send_bedbug_bedroom_count_prompt(to: str, phone_number_id: str):
    """
    Prompts user to specify how many bedrooms are affected.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Number of Bedrooms Affected" },
            "body":   { "text": "How many bedrooms are affected by bedbugs?" },
            "footer": { "text": "Select an option" },
            "action": {
                "button": "Select Count",
                "sections": [ {
                    "title": "Bedroom Count Options",
                    "rows": [
                        { "id": "bedbug_bed_count_1", "title": "1 Bedroom",   "description": "1 Bedroom affected"   },
                        { "id": "bedbug_bed_count_2", "title": "2 Bedrooms",  "description": "2 Bedrooms affected" },
                        { "id": "bedbug_bed_count_3", "title": "3+ Bedrooms", "description": "3 or more Bedrooms"  }
                    ]
                } ]
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(BEDBUG_PREFIX, to) or {}
    state["step"] = "bedbug_waiting_bedroom_count"
    set_user_state(BEDBUG_PREFIX, to, state)

# ─── 4) Overall Bedbug Count Prompt ──────────────────────────────────────────
def send_bedbug_count_prompt(to: str, phone_number_id: str):
    """
    Prompts user to estimate how many bedbugs were seen.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Bedbug Count" },
            "body":   { "text": "Please indicate roughly how many bedbugs you've seen:" },
            "footer": { "text": "Select an option" },
            "action": {
                "button": "Select Count",
                "sections": [ {
                    "title": "Bedbug Count Options",
                    "rows": [
                        { "id": "bedbug_count_feel",    "title": "Not seen, but felt",      "description": "I have felt them but haven't seen any." },
                        { "id": "bedbug_count_1to10",   "title": "1–10 Spotted",            "description": "Between 1 and 10 bedbugs."      },
                        { "id": "bedbug_count_11to30",  "title": "11–30 Spotted",           "description": "Between 11 and 30 bedbugs."     },
                        { "id": "bedbug_count_more30",  "title": "More than 30 Spotted",    "description": "Over 30 bedbugs."              },
                        { "id": "bedbug_count_others",  "title": "Others",                  "description": "Specify approximate number."   }
                    ]
                } ]
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(BEDBUG_PREFIX, to) or {}
    state["step"] = "bedbug_waiting_count_selection"
    set_user_state(BEDBUG_PREFIX, to, state)

# ─── 5) “Add Another Area?” Confirmation ──────────────────────────────────────
def send_bedbug_area_add_confirmation(to: str, phone_number_id: str):
    """
    After any area (except bedroom count), ask if user wants to add another area.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": { "text": "Would you like to add another affected area?" },
            "action": {
                "buttons": [
                    { "type": "reply", "reply": { "id": "bedbug_add_area_yes", "title": "Yes" }  },
                    { "type": "reply", "reply": { "id": "bedbug_add_area_no",  "title": "No"  }  }
                ]
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(BEDBUG_PREFIX, to) or {}
    state["step"] = "bedbug_waiting_area_add_confirmation"
    set_user_state(BEDBUG_PREFIX, to, state)

# ─── 6) Summary & Confirmation ───────────────────────────────────────────────
def send_bedbug_summary(to: str, phone_number_id: str):
    """
    Summarizes all collected bedbug details and asks for final confirmation.
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

    summary += f"\nBedroom(s) affected: {bedroom_count}\n"
    summary += f"Bedbug Count: {overall_count}\n\n"
    summary += "Please confirm the above information. Once confirmed, we will connect you to our agent."

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": { "text": summary },
            "action": {
                "buttons": [
                    { "type": "reply", "reply": { "id": "bedbug_confirm_yes", "title": "Yes" } },
                    { "type": "reply", "reply": { "id": "bedbug_confirm_no",  "title": "No"  } }
                ]
            }
        }
    }
    send_interactive_message(payload)

    state["step"] = "bedbug_waiting_confirmation"
    set_user_state(BEDBUG_PREFIX, to, state)

# ─── 7) Interactive Bedbug FAQ List ───────────────────────────────────────────
def send_bedbug_faq_list(to: str, phone_number_id: str):
    """
    Sends an interactive list of Bedbug‐related FAQs.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Bed Bug FAQ" },
            "body":   { "text": "Select a FAQ question:" },
            "footer": { "text": "Tap an option" },
            "action": {
                "button": "Select FAQ",
                "sections": [ {
                    "title": "FAQ Questions",
                    "rows": [
                        { "id": "bbfaq_safe",        "title": "Is it Safe?",          "description": "Kids/Pets: Is the treatment safe?" },
                        { "id": "bbfaq_service",     "title": "Service Details",      "description": "What's included in heat treatment?" },
                        { "id": "bbfaq_warranty",    "title": "Warranty Details",     "description": "Coverage and terms" },
                        { "id": "bbfaq_preparation", "title": "Preparation",          "description": "How to prepare your space?" },
                        { "id": "bbfaq_payment",     "title": "Payment Options",      "description": "Payment methods accepted" }
                    ]
                } ]
            }
        }
    }
    send_interactive_message(payload)

    state = get_user_state(BEDBUG_PREFIX, to) or {}
    state["step"] = "bedbug_faq"
    set_user_state(BEDBUG_PREFIX, to, state)

def process_bedbug_faq_response(to: str, faq_id: str):
    """
    After tapping one of the FAQ rows, send back the corresponding answer as text,
    then re‐send the FAQ list so user can pick another question.
    """
    faq_answers = {
        "bbfaq_safe": (
            "Absolutely! At Four Solutions, we offer a completely chemical‐free treatment using advanced professional heaters.\n\n"
            "Our heat treatment method effectively eliminates all stages of bed bugs, including eggs, in a single session—without any pesticides or chemicals.\n\n"
            "This ensures that you, your children, and your pets remain safe throughout and after the treatment."
        ),
        "bbfaq_service": (
            "Our comprehensive heat treatment service includes:\n\n"
            "1) **Initial assessment** to identify hotspots.\n"
            "2) **Professional setup** of heating equipment.\n"
            "3) **Heat treatment process** (~2–4 hours depending on size/severity).\n"
            "4) **Continuous monitoring** to ensure corners and crevices reach target temperature.\n"
            "5) **Final inspection** to confirm complete eradication.\n"
            "6) **Warranty coverage** after completion (see Warranty FAQ for details).\n\n"
            "Note: Cleaning (removal of dead bed bugs) is not included."
        ),
        "bbfaq_warranty": (
            "Four Solutions offers 100% warranty coverage on all fully treated areas, supported by our 100% money‐back guarantee.\n\n"
            "**Important:** If you choose partial treatment (e.g., treating only one bedroom when multiple rooms are infested),\n"
            "full warranty coverage may not apply due to reinfestation risk.\n\n"
            "**Warranty Includes:**\n"
            "• Unlimited re‐treatments of the treated areas for 6 months from the initial treatment date.\n"
            "• 100% money‐back guarantee if bed bugs persist after 4 treatment attempts (proof of infestation required).\n"
            "• Note: Opting for money‐back voids the unlimited re‐treatment option."
        ),
        "bbfaq_preparation": (
            "Preparation (What to do before our arrival):\n\n"
            "1) Note down locations and approximate count of bedbugs—share with the technician upon arrival.\n"
            "2) Remove heat‐sensitive items (creams, cosmetics, wax products, food items, sensitive artwork).\n"
            "   (We are not responsible for damage to items left in the treatment area.)\n"
            "3) Unplug and remove electronics from treatment areas to allow clear access.\n"
            "4) Minimize the number of occupants during treatment for safety and comfort.\n"
            "5) Clear clutter so our equipment and technician can work efficiently.\n\n"
            "**Arrival:** We aim to arrive within 1 hour of the scheduled time. Any delays will be communicated promptly."
        ),
        "bbfaq_payment": (
            "We accept the following payment methods:\n\n"
            "• **PayNow**: UEN 201812722M\n"
            "• **Atome**: Interest‐free installment for 3 months (5% surcharge applies)\n"
            "• **Cash**: Please inform us in advance if you need to pay in cash and prepare the exact amount."
        )
    }

    answer = faq_answers.get(faq_id, "Sorry, no information is available for that question.")
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": answer }
    })

    # After sending the answer, re‐send the FAQ list so user can pick another question
    send_bedbug_faq_list(to, os.getenv("PHONE_NUMBER_ID"))


# ─── 8) Helper: If “Bedroom(s)” was chosen, but count not yet asked ─────────────
def _maybe_ask_bedroom_count(to: str, phone_number_id: str):
    """
    If “Bedroom(s)” is among affected_areas but bedroom_count not filled:
      → ask bedroom count. Otherwise, move on to overall count.
    """
    state = get_user_state(BEDBUG_PREFIX, to) or {}
    areas = state.get("affected_areas", [])

    if "Bedroom(s)" in areas and "bedbug_bedroom_count" not in state:
        send_bedbug_bedroom_count_prompt(to, phone_number_id)
    elif "bedbug_count" not in state:
        send_bedbug_count_prompt(to, phone_number_id)
    else:
        # All counts collected → show summary
        send_bedbug_summary(to, phone_number_id)


# ─── 9) Main Flow‐Handler: handle_bedbug_flow ─────────────────────────────────
def handle_bedbug_flow(from_number: str, message: dict, user_state: dict):
    """
    Main driver for the Bedbug flow. 
    Called by dispatcher.py when Redis state for prefix="bedbug" exists 
    (or when 'Need help on Bedbugs!' is tapped).
    """
    state = user_state or {}
    step  = state.get("step", "")
    msg_type = message.get("type")  # "text", "button" or "interactive"

    # Helper to extract quick‐reply button payload
    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"]["payload"]
        if (msg.get("type") == "interactive" 
                and msg["interactive"].get("type") == "button_reply"):
            return msg["interactive"]["button_reply"]["id"]
        return ""

    # ─── A) If user taps any FAQ (list_reply ID starts with "bbfaq_"), show answer ───
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id = message["interactive"]["list_reply"]["id"]
        if choice_id.startswith("bbfaq_"):
            print(f"[DEBUG] handle_bedbug_flow: LIST payload='{choice_id}' from {from_number}")
            process_bedbug_faq_response(from_number, choice_id)
            return

    # ─── B) Handle BUTTONS (“button” or “interactive.button_reply”) ─────────────────
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_bedbug_flow: BUTTON payload='{payload_lower}' from {from_number}")
            state = user_state or {}
            step  = state.get("step", "")

            # 1) From Main Menu: “Need help on Bedbugs!” → show the initial menu
            if payload_lower == "need help on bedbugs!":
                clear_user_state(BEDBUG_PREFIX, from_number)
                send_bedbug_option_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # 2) On the Bedbug‐option screen (step == "bedbug_option")
            if step == "bedbug_option":
                if payload_lower == "bedbug_quote":
                    # Start quoting: collect areas
                    new_state = { "step": "bedbug_select_area", "affected_areas": [] }
                    set_user_state(BEDBUG_PREFIX, from_number, new_state)
                    send_bedbug_area_selection(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                if payload_lower == "bedbug_more_info":
                    # Show FAQ
                    state["step"] = "bedbug_faq"
                    set_user_state(BEDBUG_PREFIX, from_number, state)
                    send_bedbug_faq_list(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                if payload_lower == "return_main_menu":
                    clear_user_state(BEDBUG_PREFIX, from_number)
                    from flows.car_fumigation import send_main_menu  # noqa: F401
                    send_main_menu(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                # Unrecognized button on bedbug_option
                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "Sorry, I didn’t understand that. Type 'reset' to start over." }
                })
                return

            # 3) “Add Another Area?” confirmation (step == "bedbug_waiting_area_add_confirmation")
            if step == "bedbug_waiting_area_add_confirmation":
                if payload_lower == "bedbug_add_area_yes":
                    state["step"] = "bedbug_select_area"
                    set_user_state(BEDBUG_PREFIX, from_number, state)
                    send_bedbug_area_selection(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                if payload_lower == "bedbug_add_area_no":
                    # Remove the awaiting flag, then proceed to counts
                    if "awaiting_area_add_confirmation" in state:
                        del state["awaiting_area_add_confirmation"]
                    set_user_state(BEDBUG_PREFIX, from_number, state)
                    _maybe_ask_bedroom_count(from_number, os.getenv("PHONE_NUMBER_ID"))
                    return

                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "Please select 'Yes' or 'No'." }
                })
                return

            # 4) Bedroom‐count selection (step == "bedbug_waiting_bedroom_count")
            if step == "bedbug_waiting_bedroom_count":
                count_map = {
                    "bedbug_bed_count_1": "1 Bedroom affected",
                    "bedbug_bed_count_2": "2 Bedrooms affected",
                    "bedbug_bed_count_3": "3+ Bedrooms affected"
                }
                selected_count = count_map.get(payload, "")
                state["bedbug_bedroom_count"] = selected_count

                # Now ask if user wants to add another area
                state["step"] = "bedbug_waiting_area_add_confirmation"
                set_user_state(BEDBUG_PREFIX, from_number, state)
                send_bedbug_area_add_confirmation(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # 5) Overall‐count selection (step == "bedbug_waiting_count_selection")
            if step == "bedbug_waiting_count_selection":
                count_map = {
                    "bedbug_count_feel":   "Not seen, but felt",
                    "bedbug_count_1to10":  "1–10 spotted",
                    "bedbug_count_11to30": "11–30 spotted",
                    "bedbug_count_more30": "More than 30 spotted"
                }
                if payload == "bedbug_count_others":
                    # Ask for free‐form count text
                    state["step"] = "bedbug_waiting_count_text"
                    set_user_state(BEDBUG_PREFIX, from_number, state)
                    send_text_message({
                        "to": from_number,
                        "type": "text",
                        "messaging_product": "whatsapp",
                        "text": {
                            "body": "Please specify the approximate number of bedbugs:"
                        }
                    })
                    return

                else:
                    state["bedbug_count"] = count_map.get(payload, "")
                    # Move to final summary
                    state["step"] = "bedbug_waiting_confirmation"
                    set_user_state(BEDBUG_PREFIX, from_number, state)
                    send_bedbug_summary(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

            # 6) Final summary confirmation (step == "bedbug_waiting_confirmation")
            if step == "bedbug_waiting_confirmation":
                if payload_lower == "bedbug_confirm_yes":
                    # Connect to agent & send Bedbug FAQ
                    hold_on_text = (
                        "Hold on tight—we’re summoning a real, living, breathing, functioning human support agent for you! "
                        "They’ll join this chat as soon as they're available. In the meantime, feel free to explore our other services and read our FAQ!"
                    )
                    send_text_message({
                        "to": from_number,
                        "type": "text",
                        "messaging_product": "whatsapp",
                        "text": { "body": hold_on_text }
                    })

                    # Small delay so the FAQ isn’t dropped
                    time.sleep(1)

                    send_bedbug_faq_list(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )

                    state["step"] = "bedbug_waiting_agent"
                    set_user_state(BEDBUG_PREFIX, from_number, state)
                    return

                if payload_lower == "bedbug_confirm_no":
                    send_text_message({
                        "to": from_number,
                        "type": "text",
                        "messaging_product": "whatsapp",
                        "text": { "body": "Let's update your bedbug details. Restarting the bedbug flow." }
                    })
                    clear_user_state(BEDBUG_PREFIX, from_number)
                    send_bedbug_option_prompt(
                        to=from_number,
                        phone_number_id=os.getenv("PHONE_NUMBER_ID")
                    )
                    return

                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "Please select 'Yes' or 'No'." }
                })
                return

    # ─── C) Handle interactive LIST replies (“interactive.list_reply”) ─────────────
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id    = message["interactive"]["list_reply"]["id"]
        choice_title = message["interactive"]["list_reply"].get("title", "")
        print(f"[DEBUG] handle_bedbug_flow: LIST payload='{choice_id}' from {from_number}")

        state = user_state or {}
        step  = state.get("step", "")

        # 1) Picking an affected area (step == "bedbug_waiting_area_selection")
        if step == "bedbug_waiting_area_selection":
            state.setdefault("affected_areas", [])

            if choice_id == "bedbug_area_others":
                # Ask user to specify a custom area by text
                state["step"] = "bedbug_waiting_other_area"
                set_user_state(BEDBUG_PREFIX, from_number, state)
                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "Please specify the affected area:" }
                })
                return

            # If user chose Bedroom(s)
            if choice_id == "bedbug_area_bed":
                state["affected_areas"].append("Bedroom(s)")
                set_user_state(BEDBUG_PREFIX, from_number, state)
                send_bedbug_bedroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # Else for other fixed areas
            area_map = {
                "bedbug_area_living":     "Living Area",
                "bedbug_area_whole":      "Whole Unit",
                "bedbug_area_commercial": "Commercial Space"
            }
            selected_area = area_map.get(choice_id, "")
            if selected_area:
                state["affected_areas"].append(selected_area)
                set_user_state(BEDBUG_PREFIX, from_number, state)

            # Ask if user wants to add another area
            state["step"] = "bedbug_waiting_area_add_confirmation"
            set_user_state(BEDBUG_PREFIX, from_number, state)
            send_bedbug_area_add_confirmation(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # ─── D) Handle plain‐text input for “Others” or custom count ─────────────────
    if msg_type == "text":
        text_body = message["text"]["body"].strip()
        state     = user_state or {}
        step      = state.get("step", "")

        # 1) If waiting for a custom “Other area” name
        if step == "bedbug_waiting_other_area":
            state.setdefault("affected_areas", []).append("Other: " + text_body)
            # After custom area, ask if they want to add more areas
            state["step"] = "bedbug_waiting_area_add_confirmation"
            set_user_state(BEDBUG_PREFIX, from_number, state)
            send_bedbug_area_add_confirmation(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # 2) If waiting for a custom bedbug count number
        if step == "bedbug_waiting_count_text":
            state["bedbug_count"] = text_body
            state["step"] = "bedbug_waiting_confirmation"
            set_user_state(BEDBUG_PREFIX, from_number, state)
            send_bedbug_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # ─── E) FALLBACK: If nothing matched above ──────────────────────────────────
    send_text_message({
        "to": from_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Sorry, I can’t handle that type of message. Type 'reset' to start over." }
    })
