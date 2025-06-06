# flows/mold.py

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


# ────────────────────────────────────────────────────────────────────────────────
# send_mold_removal_faq: Step 1 (Interactive FAQ for Mold Removal)
# ────────────────────────────────────────────────────────────────────────────────
def send_mold_removal_faq(to: str) -> dict:
    """
    Sends an interactive FAQ list for Mold Removal.
    """
    header = "Mold Removal FAQ"
    body = "Select a FAQ question:"
    footer = "Tap an option"
    action_button = "Select FAQ"

    sections = [
        {
            "title": "FAQ Questions",
            "rows": [
                {"id": "mfaq_safe",        "title": "Is it safe? Kids/Pets",       "description": "Are treatments safe?"           },
                {"id": "mfaq_included",    "title": "Service Details",            "description": "What's included in our service?" },
                {"id": "mfaq_warranty",    "title": "Warranty Details",           "description": "Coverage & terms"                },
                {"id": "mfaq_preparation", "title": "Preparation",                "description": "How to prepare your space?"       },
                {"id": "mfaq_duration",    "title": "Service Duration",           "description": "How long does it take?"          },
                {"id": "mfaq_payment",     "title": "Payment Options",            "description": "Payment methods accepted"        }
            ]
        }
    ]

    resp = send_list_message(
        to=to,
        body="Please select a FAQ question:",
        header=header,
        footer=footer,
        action_button=action_button,
        sections=sections
    )
    print(f"[DEBUG] send_mold_removal_faq → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# process_mold_faq_response: After user selects one of the mfaq_ rows
# ────────────────────────────────────────────────────────────────────────────────
def process_mold_faq_response(to: str, faq_id: str) -> None:
    faq_answers = {
        "mfaq_safe": (
            "Yes—our mold removal and anti-mold paint treatments are safe for children and pets.\n\n"
            "We’ve serviced schools, labs, and hospitals. The anti-mold paint is odorless."
        ),
        "mfaq_included": (
            "Our mold removal service includes:\n"
            "• Protection of flooring, furniture, and fittings\n"
            "• Chemical remediation: scrubbing & removal of dead mold\n"
            "• Complimentary booklice removal (NEA-licensed)\n"
            "• Two coats of odorless anti-mold paint"
        ),
        "mfaq_warranty": (
            "Warranty coverage runs 6–12 months, depending on package.\n\n"
            "Includes one inspection and one complimentary re-treatment if needed."
        ),
        "mfaq_preparation": (
            "To prepare:\n"
            "• Remove loose items from treatment areas\n"
            "• Remove curtains from windows\n"
            "• Ensure access to equipment (ladders, fans, etc.)\n"
            "• Inform technician of any concealed areas (cabinets, etc.)"
        ),
        "mfaq_duration": (
            "Typical durations:\n"
            "• Bedroom: 2–5 hours\n"
            "• Bathroom: 1–3 hours\n"
            "• Multiple areas: Technician will advise upon inspection"
        ),
        "mfaq_payment": (
            "We accept:\n"
            "• PayNow (UEN: 201812722M)\n"
            "• Atome (3-month interest-free, 5% surcharge)\n"
            "• Cash (exact amount)"
        )
    }
    answer = faq_answers.get(faq_id, "Sorry, no information is available for that question.")
    send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": answer}
    })


# ────────────────────────────────────────────────────────────────────────────────
# send_mold_option_prompt: Step 2: “Request Quotation / More Info / Return”
# ────────────────────────────────────────────────────────────────────────────────
def send_mold_option_prompt(to: str) -> dict:
    """
    Sends the initial Mold Remediation options as simple text.
    """
    text = (
        "We’re happy to help with Mold Remediation!\n\n"
        "Type:\n"
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
    print(f"[DEBUG] send_mold_option_prompt(text) → {resp}")
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# send_mold_area_selection: Step 3: Show “Select 1 or multiple areas” list
# ────────────────────────────────────────────────────────────────────────────────
def send_mold_area_selection(to: str) -> dict:
    """
    Lists all MOLD_AREAS as a WhatsApp interactive list.
    """
    header = "Mold Affected Areas"
    body = "Select 1 or multiple areas affected by mold (1 entry at a time):"
    footer = "Select Area"
    action_button = "Select Area"

    available = MOLD_AREAS  # we’ll filter out any already-selected areas below

    # If the user has already chosen some areas, filter those out:
    state = get_user_state(MOLD_PREFIX, to) or {}
    selected_titles = state.get("affected_areas", [])
    available = [area for area in MOLD_AREAS if area["title"] not in selected_titles]

    if not available:
        # If everything is already selected, skip to growth location step:
        return send_mold_growth_location(to)

    sections = [
        {
            "title": "Affected Areas",
            "rows": [
                {
                    "id": area["id"],
                    "title": area["title"],
                    "description": area["description"]
                }
                for area in available
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
    print(f"[DEBUG] send_mold_area_selection → {resp}")

    # Mark our state that we’re now waiting for a list reply:
    state["step"] = "mold_waiting_area_selection"
    set_user_state(MOLD_PREFIX, to, state)
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# send_bedroom_count_prompt: After “Bedroom,” ask how many bedrooms
# ────────────────────────────────────────────────────────────────────────────────
def send_bedroom_count_prompt(to: str) -> dict:
    payload = {
        "type": "interactive",
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Number of Bedrooms Affected"},
            "body":   {"text": "How many bedrooms are affected?"},
            "footer": {"text": "Select an option"},
            "action": {
                "button": "Select Count",
                "sections": [{
                    "title": "Bedroom Count",
                    "rows": [
                        {"id": "bedroom_count_1", "title": "1 bedroom",          "description": "One bedroom affected"},
                        {"id": "bedroom_count_2", "title": "2 bedrooms",         "description": "Two bedrooms affected"},
                        {"id": "bedroom_count_3", "title": "3 bedrooms or more", "description": "Three or more bedrooms affected"}
                    ]
                }]
            }
        }
    }
    # We can’t call send_interactive_message; instead we translate it to send_list_message:
    header = "Number of Bedrooms Affected"
    body = "How many bedrooms are affected?"
    footer = "Select an option"
    action_button = "Select Count"
    sections = [
        {
            "title": "Bedroom Count",
            "rows": [
                {"id": "bedroom_count_1", "title": "1 bedroom",          "description": "One bedroom affected"},
                {"id": "bedroom_count_2", "title": "2 bedrooms",         "description": "Two bedrooms affected"},
                {"id": "bedroom_count_3", "title": "3 bedrooms or more", "description": "Three or more bedrooms affected"}
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
    print(f"[DEBUG] send_bedroom_count_prompt(list) → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bedroom_count"
    set_user_state(MOLD_PREFIX, to, state)
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# send_bathroom_count_prompt: After “Bathroom,” ask how many bathrooms
# ────────────────────────────────────────────────────────────────────────────────
def send_bathroom_count_prompt(to: str) -> dict:
    header = "Number of Bathrooms Affected"
    body = "How many bathrooms are affected?"
    footer = "Select an option"
    action_button = "Select Count"
    sections = [
        {
            "title": "Bathroom Count",
            "rows": [
                {"id": "bathroom_count_1", "title": "1 bathroom",          "description": "One bathroom affected"},
                {"id": "bathroom_count_2", "title": "2 bathrooms",         "description": "Two bathrooms affected"},
                {"id": "bathroom_count_3", "title": "3 bathrooms or more", "description": "Three or more bathrooms affected"}
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
    print(f"[DEBUG] send_bathroom_count_prompt(list) → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_bathroom_count"
    set_user_state(MOLD_PREFIX, to, state)
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# send_add_area_confirmation_prompt: After selecting an area (not bedroom/bathroom)
# ────────────────────────────────────────────────────────────────────────────────
def send_add_area_confirmation_prompt(to: str) -> dict:
    header = ""
    body = "Would you like to add another affected area?"
    footer = ""
    action_button = "Select Option"
    sections = [
        {
            "title": "Add Another?",
            "rows": [
                {"id": "add_area_yes", "title": "Yes", "description": "Yes, add another area."},
                {"id": "add_area_no",  "title": "No",  "description": "No, I’m done."}
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
    print(f"[DEBUG] send_add_area_confirmation_prompt(list) → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_add_area_confirmation"
    set_user_state(MOLD_PREFIX, to, state)
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# send_mold_growth_location: Step 4: “Where did you spot mold?” list
# ────────────────────────────────────────────────────────────────────────────────
def send_mold_growth_location(to: str) -> dict:
    header = "Mold Growth Location"
    body = "Where did you spot the mold growth? Select one:"
    footer = "Choose an option"
    action_button = "Select Location"
    sections = [
        {
            "title": "Growth Options",
            "rows": [
                {"id": "growth_ceiling", "title": "Ceiling only",       "description": "Mold on ceiling"},
                {"id": "growth_walls",   "title": "Walls only",         "description": "Mold on walls"},
                {"id": "growth_both",    "title": "Walls and ceiling",  "description": "Mold on both"},
                {"id": "growth_others",  "title": "Others",             "description": "Enter custom location"}
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
    print(f"[DEBUG] send_mold_growth_location(list) → {resp}")

    state = get_user_state(MOLD_PREFIX, to) or {}
    state["step"] = "mold_waiting_growth_location"
    set_user_state(MOLD_PREFIX, to, state)
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# send_mold_removal_summary: Step 5: Summarize & ask “Yes/No” to confirm
# ────────────────────────────────────────────────────────────────────────────────
def send_mold_removal_summary(to: str) -> dict:
    state = get_user_state(MOLD_PREFIX, to) or {}
    data  = state

    summary = "Summary of your mold removal request:\n\nAffected Areas Reported:\n"
    for idx, area in enumerate(data.get("affected_areas", []), start=1):
        summary += f"{idx}.) {area}\n"

    if data.get("bedroom_count"):
        summary += f"\nBedrooms affected: {data['bedroom_count']}\n"
    if data.get("bathroom_count"):
        summary += f"Bathrooms affected: {data['bathroom_count']}\n"

    if data.get("growth_location"):
        growth_map = {
            "growth_ceiling": "Ceiling only",
            "growth_walls":   "Walls only",
            "growth_both":    "Walls and ceiling"
        }
        chosen = growth_map.get(data["growth_location"], data["growth_location"])
        summary += f"\nGrowth Location: {chosen}\n"

    full_text = summary + "\nType 'Yes' to confirm or 'No' to choose areas again."

    resp = send_text_message({
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": full_text}
    })
    print(f"[DEBUG] send_mold_removal_summary(text) → {resp}")

    state["step"] = "mold_waiting_confirmation"
    set_user_state(MOLD_PREFIX, to, state)
    return resp


# ────────────────────────────────────────────────────────────────────────────────
# handle_mold_flow: Full Mold flow handler
# ────────────────────────────────────────────────────────────────────────────────
def handle_mold_flow(
    from_number: str,
    message: dict,
    user_state: dict
) -> Response:
    """
    Drives the entire Mold Remediation flow. We inspect user_state["step"]
    and message type, then call the appropriate helper (send_list_message,
    send_text_message) as needed.
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

    # ── A) Handle any “list_reply” that starts with “mfaq_” (FAQ) at any step:
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id = message["interactive"]["list_reply"]["id"]
        print(f"[DEBUG] handle_mold_flow: LIST payload='{choice_id}'")
        if choice_id.startswith("mfaq_"):
            process_mold_faq_response(from_number, choice_id)
            send_mold_removal_faq(to=from_number)
            return Response(status=200)

    # ── B) If they tapped a BUTTON or interactive button_reply:
    if msg_type in ["button", "interactive"]:
        payload = extract_button_payload(message).lower()
        print(f"[DEBUG] handle_mold_flow: BUTTON payload='{payload}'")

        # 1) From Main Menu: “Need help on Mold!”
        if payload == "need help on mold!":
            clear_user_state(MOLD_PREFIX, from_number)
            new_state = { "step": "mold_option", "affected_areas": [] }
            set_user_state(MOLD_PREFIX, from_number, new_state)
            return send_mold_option_prompt(to=from_number)

        # 2) On the Mold-option screen (step == "mold_option"):
        if step == "mold_option":
            if payload in ["1", "1️⃣", "mold_get_quote"]:
                new_state = { "step": "mold_select_area", "affected_areas": [] }
                set_user_state(MOLD_PREFIX, from_number, new_state)
                return send_mold_area_selection(to=from_number)

            if payload in ["2", "2️⃣", "mold_more_info"]:
                state["step"] = "mold_faq"
                set_user_state(MOLD_PREFIX, from_number, state)
                return send_mold_removal_faq(to=from_number)

            if payload in ["3", "3️⃣", "return_main_menu"]:
                clear_user_state(MOLD_PREFIX, from_number)
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
                "text": {"body": "Sorry, I didn’t understand that. Type 'reset' to start over."}
            })
            return Response(status=200)

        # 3) “Add Another Area?” (step == "mold_waiting_add_area_confirmation"):
        if step == "mold_waiting_add_area_confirmation":
            if payload in ["add_area_yes", "yes", "y"]:
                state["step"] = "mold_select_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                return send_mold_area_selection(to=from_number)

            if payload in ["add_area_no", "no", "n"]:
                state["step"] = "mold_prompt_growth"
                set_user_state(MOLD_PREFIX, from_number, state)
                return send_mold_growth_location(to=from_number)

            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Please select 'Yes' or 'No'."}
            })
            return Response(status=200)

        # 4) Summary Confirmation (“Yes”/“No”) (step == "mold_waiting_confirmation"):
        if step == "mold_waiting_confirmation":
            if payload in ["mold_confirm_yes", "yes", "y"]:
                return alert_internal_and_ask_photos(from_number)

            if payload in ["mold_confirm_no", "no", "n"]:
                state["step"] = "mold_select_area"
                set_user_state(MOLD_PREFIX, from_number, state)
                return send_mold_area_selection(to=from_number)

            send_text_message({
                "to": from_number,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": {"body": "Please select 'Yes' or 'No'."}
            })
            return Response(status=200)

    # ── C) Handle interactive “list_reply” for non-FAQ steps:
    if msg_type == "interactive" and message["interactive"].get("type") == "list_reply":
        choice_id    = message["interactive"]["list_reply"]["id"]
        choice_title = message["interactive"]["list_reply"].get("title", "")
        print(f"[DEBUG] handle_mold_flow: LIST payload='{choice_id}'")

        # A) If step == "mold_waiting_area_selection":
        if step == "mold_waiting_area_selection":
            state.setdefault("affected_areas", []).append(choice_title)
            set_user_state(MOLD_PREFIX, from_number, state)

            if choice_id == "area_bedroom":
                state["step"] = "mold_waiting_bedroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                return send_bedroom_count_prompt(to=from_number)

            if choice_id == "area_bathroom":
                state["step"] = "mold_waiting_bathroom_count"
                set_user_state(MOLD_PREFIX, from_number, state)
                return send_bathroom_count_prompt(to=from_number)

            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            return send_add_area_confirmation_prompt(to=from_number)

        # B) After bedroom count:
        if step == "mold_waiting_bedroom_count":
            count = choice_title.split()[0]
            state["bedroom_count"] = count
            set_user_state(MOLD_PREFIX, from_number, state)

            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            return send_add_area_confirmation_prompt(to=from_number)

        # C) After bathroom count:
        if step == "mold_waiting_bathroom_count":
            count = choice_title.split()[0]
            state["bathroom_count"] = count
            set_user_state(MOLD_PREFIX, from_number, state)

            state["step"] = "mold_waiting_add_area_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            return send_add_area_confirmation_prompt(to=from_number)

        # D) After growth location:
        if step == "mold_waiting_growth_location":
            state["growth_location"] = choice_id
            set_user_state(MOLD_PREFIX, from_number, state)

            state["step"] = "mold_waiting_confirmation"
            set_user_state(MOLD_PREFIX, from_number, state)
            return send_mold_removal_summary(to=from_number)

    # ── D) FALLBACK if none of the above matched:
    send_text_message({
        "to": from_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": "Sorry, I can’t handle that. Type 'reset' to start over."}
    })
    return Response(status=200)


# ────────────────────────────────────────────────────────────────────────────────
# alert_internal_and_ask_photos: After they confirm, send internal alert & ask user photos
# ────────────────────────────────────────────────────────────────────────────────
def alert_internal_and_ask_photos(client_number: str) -> None:
    state = get_user_state(MOLD_PREFIX, client_number) or {}
    data  = state

    # Build summary block for internal alert
    area_lines = ""
    for idx, area in enumerate(data.get("affected_areas", []), start=1):
        area_lines += f"{idx}.) {area}\n"

    bedroom_info  = f"\nBedrooms affected: {data.get('bedroom_count', 'N/A')}\n" if data.get("bedroom_count") else ""
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

    # Send alert to company number and bot number
    company_no = "+6587788080"
    bot_no     = "+6588662359"
    send_text_message({
        "to": company_no,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": summary_text}
    })
    send_text_message({
        "to": bot_no,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": summary_text}
    })

    # Prompt end user to upload photos
    prompt_text = (
        "Hang tight—we’re bringing in a real, live human support agent. They’ll join shortly.\n"
        "In the meantime, please upload a wide-angle photo (from the door) capturing "
        "the entire area affected. 😊"
    )
    send_text_message({
        "to": client_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": prompt_text}
    })

    time.sleep(1)

    # Then send a quick FAQ to the user while they wait:
    send_text_message({
        "to": client_number,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": "While you wait, here’s our FAQ to learn more about our mold removal service:"}
    })
    send_mold_removal_faq(to=client_number)

    # Final internal state:
    state["step"] = "mold_waiting_agent"
    set_user_state(MOLD_PREFIX, client_number, state)
