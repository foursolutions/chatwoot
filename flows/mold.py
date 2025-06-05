# flows/mold.py

import os
import time
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message
)

# ─── Constants & Static Data ─────────────────────────────────────────────────

MOLD_PREFIX = "mold"

MOLD_AREAS = [
    { "id": "area_bedroom",    "title": "Bedroom",       "description": "Mold in bedroom(s)"       },
    { "id": "area_bathroom",   "title": "Bathroom",      "description": "Mold in bathroom(s)"      },
    { "id": "area_store",      "title": "Store/Yard",    "description": "Store Room/Service Yard"  },
    { "id": "area_living",     "title": "Living Area",   "description": "Mold in living/dining"    },
    { "id": "area_kitchen",    "title": "Kitchen",       "description": "Mold in kitchen"          },
    { "id": "area_furniture",  "title": "Furniture",     "description": "Mold on furniture"        },
    { "id": "area_entire",     "title": "Entire Unit",   "description": "Whole unit affected"      },
    { "id": "area_smell",      "title": "Mold Smell",    "description": "Odor detected"            },
    { "id": "area_commercial", "title": "Commercial",    "description": "Office/shop affected"     },
    { "id": "area_others",     "title": "Other Areas",   "description": "Unlisted areas"           }
]


# ─── 1) FAQ Section ──────────────────────────────────────────────────────────
def send_mold_removal_faq(to: str, phone_number_id: str):
    """
    Sends an interactive FAQ list for Mold Removal, using your updated questions
    and descriptions.
    """
    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Mold Removal FAQ" },
        "body":   { "text": "Select a FAQ question:" },
        "footer": { "text": "Tap an option" },
        "action": {
            "button": "Select FAQ",
            "sections": [ {
                "title": "FAQ Questions",
                "rows": [
                    { "id": "mfaq_safe",        "title": "Is it safe? Kids/Pets",        "description": "Are treatments safe for kids and pets?" },
                    { "id": "mfaq_included",    "title": "Service Details",             "description": "What's included in our service?"       },
                    { "id": "mfaq_warranty",    "title": "Warranty Details",            "description": "Coverage and terms"                    },
                    { "id": "mfaq_preparation", "title": "Preparation",                 "description": "How to prepare your space?"            },
                    { "id": "mfaq_duration",    "title": "Service Duration",            "description": "How long does it take?"               },
                    { "id": "mfaq_payment",     "title": "Payment Options",             "description": "Payment methods accepted"              }
                ]
            } ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_mold_removal_faq → {resp}")


def process_mold_faq_response(to: str, faq_id: str):
    """
    After the user taps one of the FAQ rows, send back the corresponding answer.
    Uses your updated answer text.
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
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": answer }
    })


# ─── 2) “Request a Quotation” / Option Prompt ─────────────────────────────────
def send_mold_option_prompt(to: str, phone_number_id: str):
    """
    Sends the initial “Mold Remediation” options:
      • Request a Quotation
      • More Info on Service
      • Return to Main Menu
    """
    text = "We are happy to help! Select an option below for us to better understand what you are looking for!"
    interactive_payload = {
        "type": "button",
        "body": { "text": text },
        "action": {
            "buttons": [
                { "type": "reply", "reply": { "id": "mold_get_quote",    "title": "Request a Quotation"   } },
                { "type": "reply", "reply": { "id": "mold_more_info",     "title": "More Info on Service"  } },
                { "type": "reply", "reply": { "id": "return_main_menu",  "title": "Return to Main Menu"   } }
            ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_mold_option_prompt → {resp}")


# ─── 3) “Select Mold Area” → Interactive List ─────────────────────────────────
def send_mold_area_selection(to: str, phone_number_id: str):
    """
    Step: List out all MOLD_AREAS as a WhatsApp interactive list, one entry at a time.
    """
    state    = get_user_state(MOLD_PREFIX, to) or {}
    selected = state.get("affected_areas", [])

    # Filter out already‐selected area titles
    available = [area for area in MOLD_AREAS if area["title"] not in selected]
    if not available:
        # If nothing left to choose, move to growth location
        send_mold_growth_location(to, phone_number_id)
        return

    rows = [
        { "id": area["id"], "title": area["title"], "description": area["description"] }
        for area in available
    ]
    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Mold Affected Areas" },
        "body":   { "text": "Select 1 or multiple areas affected by mold (1 entry at a time):" },
        "footer": { "text": "Select Area" },
        "action": {
            "button": "Select Area",
            "sections": [ { "title": "Affected Areas", "rows": rows } ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_mold_area_selection → {resp}")

    # Mark in Redis that we’re awaiting a list reply for the area selection
    state["step"] = "mold_waiting_area_selection"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 4) Bedroom / Bathroom Count Prompts ──────────────────────────────────────
def send_bedroom_count_prompt(to: str, phone_number_id: str):
    """
    After the user picks “Bedroom,” ask how many bedrooms are affected.
    """
    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Number of Bedrooms Affected" },
        "body":   { "text": "How many bedrooms are affected?" },
        "footer": { "text": "Select an option" },
        "action": {
            "button": "Select Count",
            "sections": [ {
                "title": "Bedroom Count",
                "rows": [
                    { "id": "bedroom_count_1", "title": "1 bedroom",          "description": "One bedroom affected"            },
                    { "id": "bedroom_count_2", "title": "2 bedrooms",         "description": "Two bedrooms affected"           },
                    { "id": "bedroom_count_3", "title": "3 bedrooms or more", "description": "Three or more bedrooms affected" }
                ]
            } ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_bedroom_count_prompt → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bedroom_count"
    set_user_state(MOLD_PREFIX, to, state)


def send_bathroom_count_prompt(to: str, phone_number_id: str):
    """
    After the user picks “Bathroom,” ask how many bathrooms are affected.
    """
    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Number of Bathrooms Affected" },
        "body":   { "text": "How many bathrooms are affected?" },
        "footer": { "text": "Select an option" },
        "action": {
            "button": "Select Count",
            "sections": [ {
                "title": "Bathroom Count",
                "rows": [
                    { "id": "bathroom_count_1", "title": "1 bathroom",          "description": "One bathroom affected"            },
                    { "id": "bathroom_count_2", "title": "2 bathrooms",         "description": "Two bathrooms affected"           },
                    { "id": "bathroom_count_3", "title": "3 bathrooms or more", "description": "Three or more bathrooms affected" }
                ]
            } ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_bathroom_count_prompt → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bathroom_count"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 5) Confirmation of “Add Another Area?” ───────────────────────────────────
def send_add_area_confirmation_prompt(to: str, phone_number_id: str):
    """
    After any area selection (other than bedroom/bathroom), ask:
      “Would you like to add another affected area?”
    """
    interactive_payload = {
        "type": "button",
        "body": { "text": "Would you like to add another affected area?" },
        "action": {
            "buttons": [
                { "type": "reply", "reply": { "id": "add_area_yes", "title": "Yes" } },
                { "type": "reply", "reply": { "id": "add_area_no",  "title": "No"  } }
            ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_add_area_confirmation_prompt → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_add_area_confirmation"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 6) Growth Location Prompt ────────────────────────────────────────────────
def send_mold_growth_location(to: str, phone_number_id: str):
    """
    Asks: “Where did you spot the mold growth?” with a list of options.
    """
    interactive_payload = {
        "type": "list",
        "header": { "type": "text", "text": "Mold Growth Location" },
        "body":   { "text": "Where did you spot the mold growth?\nSelect one:" },
        "footer": { "text": "Choose an option" },
        "action": {
            "button": "Select Location",
            "sections": [ {
                "title": "Growth Options",
                "rows": [
                    { "id": "growth_ceiling", "title": "Ceiling only",       "description": "Mold on ceiling"         },
                    { "id": "growth_walls",   "title": "Walls only",         "description": "Mold on walls"           },
                    { "id": "growth_both",    "title": "Walls and ceiling",  "description": "Mold on both"            },
                    { "id": "growth_others",  "title": "Others",             "description": "Enter custom location"   }
                ]
            } ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_mold_growth_location → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_growth_location"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 7) Summary & Confirmation ───────────────────────────────────────────────
def send_mold_removal_summary(to: str, phone_number_id: str):
    """
    Summarizes all data collected so far, then asks “Yes”/“No” to confirm.
    """
    state = get_user_state(MOLD_PREFIX, to) or {}
    data  = state

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
    interactive_payload = {
        "type": "button",
        "body": { "text": body_text },
        "action": {
            "buttons": [
                { "type": "reply", "reply": { "id": "mold_confirm_yes", "title": "Yes" } },
                { "type": "reply", "reply": { "id": "mold_confirm_no",  "title": "No" } }
            ]
        }
    }

    resp = send_text_message({
        "to": to,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": interactive_payload
    })
    print(f"[DEBUG] send_mold_removal_summary → {resp}")

    state["step"] = "mold_waiting_confirmation"
    set_user_state(MOLD_PREFIX, to, state)


# ─── 8) Main Flow‐Handler: handle_mold_flow ────────────────────────────────────
def handle_mold_flow(from_number: str, message: dict, user_state: dict):
    """
    Drives the entire Mold Remediation flow.
    If the user taps any FAQ (mfaq_…), it will show the answer and re‐render the FAQ.
    """
    state = user_state or {}
    step  = state.get("step", "")
    msg_type = message.get("type")  # "text", "button", or "interactive"

    def extract_button_payload(msg: dict) -> str:
        if msg.get("type") == "button":
            return msg["button"]["payload"]
        if msg.get("type") == "interactive" and msg["interactive"].get("type") == "button_reply":
            return msg["interactive"]["button_reply"]["id"]
        return ""

    # ─── A) FAQ Handling at ANY STEP ─────────────────────────────────────────────
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id = message["interactive"]["list_reply"]["id"]
        if choice_id.startswith("mfaq_"):
            print(f"[DEBUG] handle_mold_flow: LIST payload='{choice_id}' from {from_number}")
            process_mold_faq_response(from_number, choice_id)
            send_mold_removal_faq(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # ─── 1) Handle BUTTONS (“button” or “interactive.button_reply”) ─────────────
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message)
        if payload:
            payload_lower = payload.lower()
            print(f"[DEBUG] handle_mold_flow: BUTTON payload='{payload_lower}' from {from_number}")
            state = user_state or {}
            step  = state.get("step", "")

            # A) From Main Menu: “Need help on Mold!”
            if payload_lower == "need help on mold!":
                clear_user_state(MOLD_PREFIX, from_number)
                new_state = { "step": "mold_option", "affected_areas": [] }
                set_user_state(MOLD_PREFIX, from_number, new_state)
                send_mold_option_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            # B) On the Mold‐option screen (step == "mold_option")
            if step == "mold_option":
                if payload_lower == "mold_get_quote":
                    new_state = { "step": "mold_select_area", "affected_areas": [] }
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

                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "Sorry, I didn’t understand that. Type 'reset' to start over." }
                })
                return

            # C) “Add Another Area?” (step == "mold_waiting_add_area_confirmation")
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

                send_text_message({
                    "to": from_number,
                    "type": "text",
                    "messaging_product": "whatsapp",
                    "text": { "body": "Please select 'Yes' or 'No'." }
                })
                return

            # D) Summary Confirmation (“Yes”/“No”) (step == "mold_waiting_confirmation")
            if step == "mold_waiting_confirmation":
                if payload_lower == "mold_confirm_yes":
                    alert_internal_and_ask_photos(from_number)
                    return

                if payload_lower == "mold_confirm_no":
                    state["step"] = "mold_select_area"
                    set_user_state(MOLD_PREFIX, from_number, state)
                    send_mold_area_selection(
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

    # ─── 2) Handle interactive LIST replies (“interactive.list_reply”) ─────────────
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id    = message["interactive"]["list_reply"]["id"]
        choice_title = message["interactive"]["list_reply"].get("title", "")
        print(f"[DEBUG] handle_mold_flow: LIST payload='{choice_id}' from {from_number}")
        state = user_state or {}
        step  = state.get("step", "")

        # A) Picking an affected area
        if step == "mold_waiting_area_selection":
            state.setdefault("affected_areas", []).append(choice_title)
            set_user_state(MOLD_PREFIX, from_number, state)

            if choice_id.startswith("area_bedroom"):
                state["step"] = "mold_waiting_bedroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bedroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            if choice_id.startswith("area_bathroom"):
                state["step"] = "mold_waiting_bathroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                send_bathroom_count_prompt(
                    to=from_number,
                    phone_number_id=os.getenv("PHONE_NUMBER_ID")
                )
                return

            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # B) After bedroom count
        if step == "mold_waiting_bedroom_count":
            count = choice_title.split()[0]
            state["bedroom_count"] = count
            set_user_state(MOLD_PREFIX, from_number, state)

            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # C) After bathroom count
        if step == "mold_waiting_bathroom_count":
            count = choice_title.split()[0]
            state["bathroom_count"] = count
            set_user_state(MOLD_PREFIX, from_number, state)

            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_add_area_confirmation_prompt(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

        # D) After growth location
        if step == "mold_waiting_growth_location":
            state["growth_location"] = choice_id
            set_user_state(MOLD_PREFIX, from_number, state)

            state["step"] = "mold_waiting_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            send_mold_removal_summary(
                to=from_number,
                phone_number_id=os.getenv("PHONE_NUMBER_ID")
            )
            return

    # ─── 3) FALLBACK: If none of the above matched ──────────────────────────────
    send_text_message({
        "to": from_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Sorry, I can’t handle that type of message. Type 'reset' to start over." }
    })


# ─── 9) INTERNAL: Alert Company & Ask for Photos (after “Yes” on summary) ───────
def alert_internal_and_ask_photos(client_number: str):
    """
    Once user confirms the summary, send the booking alert internally,
    then prompt the end user to upload wide‐angle photos, followed by an FAQ.
    """
    state = get_user_state(MOLD_PREFIX, client_number) or {}
    data  = state

    # Build summary block for internal alert
    area_lines = ""
    for idx, area in enumerate(data.get("affected_areas", []), start=1):
        area_lines += f"{idx}.) {area}\n"

    bedroom_info = f"\nBedrooms affected: {data.get('bedroom_count', 'N/A')}\n" if data.get("bedroom_count") else ""
    bathroom_info = f"Bathrooms affected: {data.get('bathroom_count', 'N/A')}\n" if data.get("bathroom_count") else ""

    growth_map = {
        "growth_ceiling": "Ceiling only",
        "growth_walls":   "Walls only",
        "growth_both":    "Walls and ceiling"
    }
    growth_text = ""
    if data.get("growth_location"):
        growth_choice = growth_map.get(data["growth_location"], data["growth_location"])
        growth_text = f"\nGrowth Location: {growth_choice}\n"

    summary_text = (
        "🚨 New Mold Enquiry Booking 🚨\n\n"
        f"Client Phone Number: +{client_number}\n\n"
        "Affected Areas Reported:\n"
        f"{area_lines}"
        f"{bedroom_info}"
        f"{bathroom_info}"
        f"{growth_text}"
    )

    # Send alert to company number and chatbot number
    company_no = "+6587788080"
    bot_no     = "+6588662359"
    send_text_message({ "to": company_no, "type": "text", "messaging_product": "whatsapp", "text": { "body": summary_text } })
    send_text_message({ "to": bot_no,     "type": "text", "messaging_product": "whatsapp", "text": { "body": summary_text } })

    # Prompt end user to upload photos
    prompt_text = (
        "Hang tight—we’re bringing in a real, live human support agent for you!\n"
        "They’ll join the chat as soon as they’re available.\n\n"
        "In the meantime, could you please take a wide-angle photo (from the door) "
        "capturing the full room or area affected? This helps us provide a rough estimate ahead of time. "
        "Just upload the images here in this chat. 😊"
    )
    send_text_message({ "to": client_number, "type": "text", "messaging_product": "whatsapp", "text": { "body": prompt_text } })

    # Small delay so the next interactive message doesn’t get dropped
    time.sleep(1)

    # “While you wait, here’s our FAQ to learn more about our mold removal service:”
    send_text_message({
        "to": client_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "While you wait, here’s our FAQ to learn more about our mold removal service:" }
    })
    send_mold_removal_faq(
        to=client_number,
        phone_number_id=os.getenv("PHONE_NUMBER_ID")
    )

    # Final internal state
    state["step"] = "mold_waiting_agent"
    set_user_state(MOLD_PREFIX, client_number, state)
