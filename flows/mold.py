import requests

# ------------------------------
# Helper Function
# ------------------------------
def send_message(payload, phone_number_id, access_token, log_msg="Sent Message"):
    """
    Reusable helper function to send a message via the WhatsApp API.
    """
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(f"✅ {log_msg}:", response.json())

# ------------------------------
# Mold Flow – Common Definitions
# ------------------------------
MOLD_AREAS = [
    {"id": "area_bedroom", "title": "Bedroom", "description": "Mold in bedroom(s)"},
    {"id": "area_bathroom", "title": "Bathroom", "description": "Mold in bathroom(s)"},
    {"id": "area_store", "title": "Store/Yard", "description": "Store Room/Service Yard"},
    {"id": "area_living", "title": "Living Area", "description": "Mold in living/dining"},
    {"id": "area_kitchen", "title": "Kitchen", "description": "Mold in kitchen"},
    {"id": "area_furniture", "title": "Furniture", "description": "Mold on furniture"},
    {"id": "area_entire", "title": "Entire Unit", "description": "Whole unit affected"},
    {"id": "area_smell", "title": "Mold Smell", "description": "Odor detected"},
    {"id": "area_commercial", "title": "Commercial", "description": "Office/shop affected"},
    {"id": "area_others", "title": "Other Areas", "description": "Unlisted areas"}
]

# ------------------------------
# Interactive FAQ Functions
# ------------------------------
def send_mold_removal_faq(to, phone_number_id, access_token, send_interactive_message):
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
                       {"id": "mfaq_safe", "title": "Is it safe? Kids/Pets", "description": "Are treatments safe for kids and pets?"},
                       {"id": "mfaq_included", "title": "Service Details", "description": "What's included in our service?"},
                       {"id": "mfaq_warranty", "title": "Warranty Details", "description": "Coverage and terms"},
                       {"id": "mfaq_preparation", "title": "Preparation", "description": "How to prepare your space?"},
                       {"id": "mfaq_duration", "title": "Service Duration", "description": "How long does it take?"},
                       {"id": "mfaq_payment", "title": "Payment Options", "description": "Payment methods accepted"}
                   ]
               }]
           }
       }
    }
    send_interactive_message(to, payload)

def process_mold_faq_response(to, faq_id, mold_removal_data, phone_number_id, access_token):
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
    
    payload = {
       "messaging_product": "whatsapp",
       "recipient_type": "individual",
       "to": to,
       "type": "text",
       "text": {"body": answer}
    }
    send_message(payload, phone_number_id, access_token, "Sent Mold FAQ Answer")

# ------------------------------
# Other Mold Flow Functions
# ------------------------------
def send_mold_option_prompt(to, phone_number_id, access_token):
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
    send_message(payload, phone_number_id, access_token, "Sent Mold Option Prompt")

def new_mold_quote_flow_start(to, mold_removal_data, phone_number_id, access_token):
    mold_removal_data[to] = {}
    send_mold_area_selection(to, mold_removal_data, phone_number_id, access_token)

def send_mold_area_selection(to, mold_removal_data, phone_number_id, access_token):
    selected = mold_removal_data.get(to, {}).get("affected_areas", [])
    available = [area for area in MOLD_AREAS if area["title"] not in selected]
    if not available:
        prompt_growth_location(to, mold_removal_data, phone_number_id, access_token)
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
    send_message(payload, phone_number_id, access_token, "Sent Mold Area Selection")
    mold_removal_data.setdefault(to, {})["awaiting_mold_area_selection"] = True

def process_mold_area_selection(to, area_id, mold_removal_data, phone_number_id, access_token, send_text_message):
    if area_id == "area_others":
        send_text_message(to, "Please specify the affected area not listed above:")
        mold_removal_data.setdefault(to, {})["awaiting_other_area"] = True
        return

    area_obj = next((a for a in MOLD_AREAS if a["id"] == area_id), None)
    if area_obj:
        mold_removal_data.setdefault(to, {}).setdefault("affected_areas", []).append(area_obj["title"])

    mold_removal_data[to].pop("awaiting_mold_area_selection", None)

    if area_id == "area_bedroom":
        send_bedroom_count_prompt(to, phone_number_id, access_token, mold_removal_data)
    elif area_id == "area_bathroom":
        send_bathroom_count_prompt(to, phone_number_id, access_token, mold_removal_data)
    else:
        send_add_area_confirmation_prompt(to, phone_number_id, access_token, mold_removal_data)

def send_bedroom_count_prompt(to, phone_number_id, access_token, mold_removal_data):
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
                       {"id": "bedroom_count_1", "title": "1 bedroom", "description": "One bedroom affected"},
                       {"id": "bedroom_count_2", "title": "2 bedrooms", "description": "Two bedrooms affected"},
                       {"id": "bedroom_count_3", "title": "3 bedrooms or more", "description": "Three or more"}
                   ]
               }]
           }
       }
    }
    send_message(payload, phone_number_id, access_token, "Sent Bedroom Count Prompt")
    mold_removal_data[to]["awaiting_bedroom_count"] = True

def send_bathroom_count_prompt(to, phone_number_id, access_token, mold_removal_data):
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
                       {"id": "bathroom_count_1", "title": "1 bathroom", "description": "One bathroom affected"},
                       {"id": "bathroom_count_2", "title": "2 bathrooms", "description": "Two bathrooms affected"},
                       {"id": "bathroom_count_3", "title": "3 bathrooms or more", "description": "Three or more"}
                   ]
               }]
           }
       }
    }
    send_message(payload, phone_number_id, access_token, "Sent Bathroom Count Prompt")
    mold_removal_data[to]["awaiting_bathroom_count"] = True

def send_add_area_confirmation_prompt(to, phone_number_id, access_token, mold_removal_data):
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
                   {"type": "reply", "reply": {"id": "add_area_no", "title": "No"}}
               ]
           }
       }
    }
    send_message(payload, phone_number_id, access_token, "Sent Add Area Confirmation Prompt")
    mold_removal_data[to]["awaiting_add_area_confirmation"] = True

def process_add_area_confirmation(to, choice, mold_removal_data, phone_number_id, access_token, send_text_message):
    if choice == "yes":
        mold_removal_data[to].pop("awaiting_add_area_confirmation", None)
        send_mold_area_selection(to, mold_removal_data, phone_number_id, access_token)
    elif choice == "no":
        mold_removal_data[to].pop("awaiting_add_area_confirmation", None)
        prompt_growth_location(to, mold_removal_data, phone_number_id, access_token)
    else:
        send_text_message(to, "Please select 'Yes' or 'No'.")

def process_other_area_text(to, text, mold_removal_data, phone_number_id, access_token, send_text_message):
    mold_removal_data.setdefault(to, {}).setdefault("affected_areas", []).append("Other: " + text)
    mold_removal_data[to].pop("awaiting_other_area", None)
    send_add_area_confirmation_prompt(to, phone_number_id, access_token, mold_removal_data)

def prompt_growth_location(to, mold_removal_data, phone_number_id, access_token):
    selected = mold_removal_data.get(to, {}).get("affected_areas", [])
    if selected and all(x in ["Mold Smell", "Furniture"] for x in selected):
        send_mold_removal_summary(to, mold_removal_data, phone_number_id, access_token)
        return
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
                       {"id": "growth_ceiling", "title": "Ceiling only", "description": "Mold on ceiling"},
                       {"id": "growth_walls", "title": "Walls only", "description": "Mold on walls"},
                       {"id": "growth_both", "title": "Walls and ceiling", "description": "Mold on both"},
                       {"id": "growth_others", "title": "Others", "description": "Enter custom location"}
                   ]
               }]
           }
       }
    }
    send_message(payload, phone_number_id, access_token, "Sent Growth Location Question")
    mold_removal_data[to]["awaiting_growth_location"] = True

def process_growth_location_choice(to, choice_id, mold_removal_data, phone_number_id, access_token, send_text_message):
    if choice_id == "growth_others":
        send_text_message(to, "Please specify the mold growth location not listed above:")
        mold_removal_data[to]["awaiting_growth_others"] = True
        return
    mold_removal_data.setdefault(to, {})["growth_location"] = choice_id
    mold_removal_data[to].pop("awaiting_growth_location", None)
    send_mold_removal_summary(to, mold_removal_data, phone_number_id, access_token)

def send_mold_removal_summary(to, mold_removal_data, phone_number_id, access_token):
    data = mold_removal_data.get(to, {})
    summary = "Summary of your mold removal request:\n\nAffected Areas Reported:\n"
    selected_areas = data.get("affected_areas", [])
    for idx, area in enumerate(selected_areas, start=1):
        summary += f"{idx}.) {area}\n"
    if "bedroom_count" in data:
        summary += f"\nBedrooms affected: {data['bedroom_count']}\n"
    if "bathroom_count" in data:
        summary += f"Bathrooms affected: {data['bathroom_count']}\n"
    if "growth_location" in data:
        growth_map = {
            "growth_ceiling": "Ceiling only",
            "growth_walls": "Walls only",
            "growth_both": "Walls and ceiling"
        }
        chosen_text = growth_map.get(data["growth_location"], data["growth_location"])
        summary += f"\nGrowth Location: {chosen_text}\n"
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
    send_message(payload, phone_number_id, access_token, "Sent Mold Removal Summary with Confirmation Buttons")
    mold_removal_data[to]["awaiting_mold_confirmation"] = True

def send_entire_unit_inspection_prompt(to, phone_number_id, access_token):
    text = (
        "Since you have selected the Entire Unit, it may be better for us to arrange an onsite inspection "
        "to understand the condition and severity of the mold. This allows us to give a more accurate quote.\n\n"
        "Do note there is a $20 onsite inspection fee, which can be waived if you engage our services."
    )
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
                    {"type": "reply", "reply": {"id": "onsite_inspect_yes", "title": "Yes, Inspect"}},
                    {"type": "reply", "reply": {"id": "onsite_inspect_no", "title": "No, Later"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Entire Unit Inspection Prompt")

def process_mold_confirmation(to, choice, mold_removal_data, phone_number_id, access_token, send_text_message, initiate_live_agent, sender_name):
    """
    Processes the user's response on the mold removal summary confirmation.
    If 'Yes' is selected, summons a live agent.
    If 'No' is selected, prompts the user to update mold details.
    """
    if choice == "mold_confirm_yes":
        message = (
            "Hold on tight—we’re summoning a real, living, breathing, functioning human support agent for you! "
            "They’ll join this chat as soon as they're available. In the meantime, feel free to explore our other services and read our FAQ!"
        )
        send_text_message(to, message)
        # Optionally call: initiate_live_agent(to, sender_name)
    elif choice == "mold_confirm_no":
        send_text_message(to, "Let's update your mold details. Please select 'Request a Quotation' to restart.")
        mold_removal_data.pop(to, None)

# ------------------------------
# Optional: Entry Point for the Mold Flow
# ------------------------------
def run_flow(to, phone_number_id, access_token, mold_removal_data, send_text_message, send_interactive_message, initiate_live_agent=None, sender_name="User"):
    """
    Entry point for the mold removal flow.
    This function initializes the mold removal data and starts the quote flow.
    """
    # For example, start by sending the mold option prompt.
    send_mold_option_prompt(to, phone_number_id, access_token)
    # Alternatively, to start the quote flow directly:
    # new_mold_quote_flow_start(to, mold_removal_data, phone_number_id, access_token)

# End of mold_flow.py


