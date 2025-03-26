import requests

# ------------------------------
# Reusable Helper Function
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
# Bedbug Flow Global Definitions
# ------------------------------
BEDBUG_AREAS = [
    {"id": "bedbug_area_bed", "title": "Bedroom(s)", "description": "Bedbugs in bedroom(s)"},
    {"id": "bedbug_area_living", "title": "Living Area", "description": "Bedbugs in living area"},
    {"id": "bedbug_area_whole", "title": "Whole Unit", "description": "Bedbugs all over the unit"},
    {"id": "bedbug_area_commercial", "title": "Commercial Space", "description": "Bedbugs in commercial space"},
    {"id": "bedbug_area_others", "title": "Others", "description": "Other areas (specify)"}
]

# ------------------------------
# Bedbug Flow Functions
# ------------------------------
def send_bedbug_initial_menu(to, phone_number_id, access_token):
    """
    Sends the initial menu for the bedbug flow with three options:
      1) Request a Quotation
      2) More Info on Service (will show the new FAQ list)
      3) Return to Main Menu
    """
    text = "We are happy to help with your bedbugs issue! Select an option below for us to better understand what you are looking for!"
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
                    {
                        "type": "reply",
                        "reply": {"id": "bedbug_quote", "title": "Request a Quotation"}
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "bedbug_more_info", "title": "More Info on Service"}
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "return_main_menu", "title": "Return to Main Menu"}
                    }
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Bedbug Initial Menu")

def send_bedbug_area_selection(to, phone_number_id, access_token, bedbug_data):
    text = "Select 1 or multiple areas affected by bedbugs (1 entry at a time):"
    selected = bedbug_data.get(to, {}).get("affected_areas", [])
    available = [option for option in BEDBUG_AREAS if option["title"] not in selected]
    rows = []
    for option in available:
        rows.append({
            "id": option["id"],
            "title": option["title"],
            "description": option["description"]
        })
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Bedbug Affected Areas"},
            "body": {"text": text},
            "footer": {"text": "Select Area"},
            "action": {
                "button": "Select Area",
                "sections": [{
                    "title": "Affected Areas",
                    "rows": rows
                }]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Bedbug Area Selection")
    bedbug_data.setdefault(to, {})["awaiting_area_selection"] = True

def process_bedbug_area_selection(to, area_id, bedbug_data, phone_number_id, access_token, send_text_message):
    if to not in bedbug_data:
        bedbug_data[to] = {}
    if "affected_areas" not in bedbug_data[to]:
        bedbug_data[to]["affected_areas"] = []
    if area_id == "bedbug_area_others":
        send_text_message(to, "Please specify the affected area:")
        bedbug_data[to]["awaiting_other_area"] = True
    elif area_id == "bedbug_area_bed":
        bedbug_data[to]["affected_areas"].append("Bedroom(s)")
        send_bedbug_bedroom_count_prompt(to, phone_number_id, access_token, bedbug_data)
    else:
        area_map = {
            "bedbug_area_living": "Living Area",
            "bedbug_area_whole": "Whole Unit",
            "bedbug_area_commercial": "Commercial Space"
        }
        selected_area = area_map.get(area_id, area_id)
        bedbug_data[to]["affected_areas"].append(selected_area)
        send_bedbug_area_add_confirmation(to, phone_number_id, access_token, bedbug_data)

def process_bedbug_area_text(to, text, bedbug_data, phone_number_id, access_token, send_text_message):
    bedbug_data.setdefault(to, {}).setdefault("affected_areas", []).append("Other: " + text)
    if "awaiting_other_area" in bedbug_data[to]:
        del bedbug_data[to]["awaiting_other_area"]
    send_bedbug_area_add_confirmation(to, phone_number_id, access_token, bedbug_data)

def process_bedbug_text_message(to, text, bedbug_data, phone_number_id, access_token, send_text_message):
    if bedbug_data.get(to, {}).get("awaiting_other_area"):
        process_bedbug_area_text(to, text, bedbug_data, phone_number_id, access_token, send_text_message)

def send_bedbug_area_add_confirmation(to, phone_number_id, access_token, bedbug_data):
    text = "Would you like to add another affected area?"
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
                    {"type": "reply", "reply": {"id": "bedbug_add_area_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "bedbug_add_area_no", "title": "No"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Bedbug Area Add Confirmation")
    bedbug_data[to]["awaiting_area_add_confirmation"] = True

def process_bedbug_area_add_confirmation(to, choice, bedbug_data, phone_number_id, access_token, send_text_message):
    if choice == "bedbug_add_area_yes":
        if "awaiting_area_add_confirmation" in bedbug_data[to]:
            del bedbug_data[to]["awaiting_area_add_confirmation"]
        send_bedbug_area_selection(to, phone_number_id, access_token, bedbug_data)
    elif choice == "bedbug_add_area_no":
        if "awaiting_area_add_confirmation" in bedbug_data[to]:
            del bedbug_data[to]["awaiting_area_add_confirmation"]
        if "Bedroom(s)" in bedbug_data[to].get("affected_areas", []) and "bedbug_bedroom_count" not in bedbug_data[to]:
            send_bedbug_bedroom_count_prompt(to, phone_number_id, access_token, bedbug_data)
        elif "bedbug_count" not in bedbug_data[to]:
            send_bedbug_count_prompt(to, phone_number_id, access_token, bedbug_data)
    else:
        send_text_message(to, "Please select 'Yes' or 'No'.")

# --- Bedroom Count Prompt ---
def send_bedbug_bedroom_count_prompt(to, phone_number_id, access_token, bedbug_data):
    text = "How many bedrooms are affected by bedbugs?"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Bedroom(s) Count"},
            "body": {"text": text},
            "footer": {"text": "Select Count"},
            "action": {
                "button": "Select Count",
                "sections": [{
                    "title": "Bedroom Count Options",
                    "rows": [
                        {"id": "bedbug_bed_count_1", "title": "1 Bedroom", "description": "1 Bedroom affected"},
                        {"id": "bedbug_bed_count_2", "title": "2 Bedrooms", "description": "2 Bedrooms affected"},
                        {"id": "bedbug_bed_count_3", "title": "3+ Bedrooms", "description": "3 or more Bedrooms affected"}
                    ]
                }]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Bedroom Count Prompt")
    bedbug_data[to]["awaiting_bedroom_count"] = True

def process_bedbug_bedroom_count_selection(to, count_id, bedbug_data, phone_number_id, access_token, send_text_message):
    count_map = {
        "bedbug_bed_count_1": "1 Bedroom affected",
        "bedbug_bed_count_2": "2 Bedrooms affected",
        "bedbug_bed_count_3": "3+ Bedrooms affected"
    }
    bedbug_data[to]["bedbug_bedroom_count"] = count_map.get(count_id, count_id)
    send_bedbug_area_add_confirmation(to, phone_number_id, access_token, bedbug_data)

# --- Overall Bedbug Count Prompt ---
def send_bedbug_count_prompt(to, phone_number_id, access_token, bedbug_data):
    text = "Please indicate roughly how many bedbugs you've seen:"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Bedbug Count"},
            "body": {"text": text},
            "footer": {"text": "Select Count"},
            "action": {
                "button": "Select Count",
                "sections": [{
                    "title": "Bedbug Count Options",
                    "rows": [
                        {
                            "id": "bedbug_count_feel",
                            "title": "Not seen, but felt",
                            "description": "(I have felt them but haven't seen any.)"
                        },
                        {
                            "id": "bedbug_count_1to10",
                            "title": "1–10 Spotted",
                            "description": "(Between 1 and 10 bedbugs.)"
                        },
                        {
                            "id": "bedbug_count_11to30",
                            "title": "11–30 Spotted",
                            "description": "(Between 11 and 30 bedbugs.)"
                        },
                        {
                            "id": "bedbug_count_more30",
                            "title": "More than 30 Spotted",
                            "description": "(Over 30 bedbugs.)"
                        },
                        {
                            "id": "bedbug_count_others",
                            "title": "Others",
                            "description": "(Specify approximate number.)"
                        }
                    ]
                }]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Overall Bedbug Count Prompt")
    bedbug_data[to]["awaiting_count_selection"] = True

def process_bedbug_count_selection(to, count_id, bedbug_data, phone_number_id, access_token, send_text_message):
    count_map = {
        "bedbug_count_feel": "Not seen, but felt",
        "bedbug_count_1to10": "1–10 spotted",
        "bedbug_count_11to30": "11–30 spotted",
        "bedbug_count_more30": "More than 30 spotted"
    }
    if count_id == "bedbug_count_others":
        send_text_message(to, "Please specify the approximate number of bedbugs:")
        bedbug_data[to]["awaiting_bedbug_count_text"] = True
    else:
        bedbug_data[to]["bedbug_count"] = count_map.get(count_id, count_id)
        send_bedbug_summary(to, bedbug_data, phone_number_id, access_token)

def send_bedbug_summary(to, bedbug_data, phone_number_id, access_token):
    data = bedbug_data.get(to, {})
    areas = data.get("affected_areas", [])
    bedroom_count = data.get("bedbug_bedroom_count", "Not provided")
    overall_count = data.get("bedbug_count", "Not provided")
    summary = "Bedbug Details Confirmation\n\n"
    summary += "Please review your details below:\n\nAffected Area(s):\n"
    if areas:
        for idx, area in enumerate(areas, start=1):
            summary += f"{idx}. {area}\n"
    else:
        summary += "None\n"
    summary += f"\nBedroom(s): {bedroom_count}\n"
    summary += f"\nBedbug Count: {overall_count}\n\n"
    summary += "Please confirm the above information. Once confirmed, we will connect you to our agent."
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": summary},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "bedbug_confirm_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "bedbug_confirm_no", "title": "No"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Bedbug Summary Confirmation")
    bedbug_data[to]["awaiting_confirmation"] = True

def process_bedbug_confirmation(
    to,
    choice,
    bedbug_data,
    phone_number_id,
    access_token,
    send_text_message,
    initiate_live_agent,
    sender_name,
    send_interactive_message=None
):
    """
    Processes the final confirmation from the user.
    If confirmed, we:
      1) Send "Hold on tight..." message
      2) Summon a live agent (if function is provided)
      3) Immediately show the Bed Bug FAQ list
    """
    if choice == "bedbug_confirm_yes":
        # 1) Send "Hold on tight..." message
        hold_on_text = (
            "Hold on tight—we’re summoning a real, living, breathing, functioning human support agent for you! "
            "They’ll join this chat as soon as they're available. In the meantime, feel free to explore our other services and read our FAQ!"
        )
        send_text_message(to, hold_on_text)

        # 2) Summon live agent
        if initiate_live_agent:
            initiate_live_agent(to, sender_name)

        # 3) Immediately show the interactive Bed Bug FAQ
        if send_interactive_message:
            send_bedbug_faq_list(to, phone_number_id, access_token, send_interactive_message)

    elif choice == "bedbug_confirm_no":
        send_text_message(to, "Let's update your bedbug details. Restarting the bedbug flow.")
        if to in bedbug_data:
            del bedbug_data[to]
        send_bedbug_initial_menu(to, phone_number_id, access_token)
    else:
        send_text_message(to, "Please select 'Yes' or 'No'.")

# ------------------------------
# Bedbug Interactive FAQ
# ------------------------------
def send_bedbug_faq_list(to, phone_number_id, access_token, send_interactive_message):
    """
    Sends an interactive list message for the bed bug FAQ.
    Each option corresponds to a FAQ question.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Bed Bug FAQ"},
            "body": {"text": "Select a FAQ question:"},
            "footer": {"text": "Tap an option"},
            "action": {
                "button": "Select FAQ",
                "sections": [{
                    "title": "FAQ Questions",
                    "rows": [
                        {
                            "id": "bbfaq_safe",
                            "title": "Is it Safe?",
                            "description": "Kids/Pets: Is the treatment safe?"
                        },
                        {
                            "id": "bbfaq_service",
                            "title": "Service Details",
                            "description": "What's included in heat treatment?"
                        },
                        {
                            "id": "bbfaq_warranty",
                            "title": "Warranty Details",
                            "description": "Coverage and terms"
                        },
                        {
                            "id": "bbfaq_preparation",
                            "title": "Preparation",
                            "description": "Tap to read more"
                        },
                        {
                            "id": "bbfaq_payment",
                            "title": "Payment Options",
                            "description": "Payment methods accepted"
                        }
                    ]
                }]
            }
        }
    }
    send_interactive_message(to, payload)

def process_bedbug_faq_response(to, faq_id, phone_number_id, access_token, send_text_message):
    """
    Processes the bedbug FAQ selection by sending the corresponding answer as a text message.
    """
    faq_answers = {
        "bbfaq_safe": (
            "Absolutely! At Four Solutions, we offer a completely chemical-free treatment using advanced professional heaters.\n\n"
            "Our heat treatment method effectively eliminates all stages of bed bugs, including eggs, in a single session—without any pesticides or chemical exposure.\n\n"
            "This ensures that you, your children, and your pets remain safe throughout and after the treatment."
        ),
        "bbfaq_service": (
            "Our comprehensive heat treatment service includes:\n\n"
            "Initial Assessment:\n"
            "• Thorough inspection to identify high-risk areas and treatment hotspots.\n\n"
            "1) Professional Setup:\n"
            "• Placement of specialized heating equipment at pre-assessed locations.\n\n"
            "2) Heat Treatment Process:\n"
            "• Heating the affected room(s) for ~2–4 hours, depending on size/severity.\n\n"
            "3) Continuous Monitoring:\n"
            "• Hourly checks to ensure corners, crevices, and bedding stay at the effective temperature.\n\n"
            "4) Final Inspection:\n"
            "• Post-treatment assessment to confirm complete eradication.\n\n"
            "5) Warranty Coverage:\n"
            "• Provided after completion (see our Warranty FAQ for details).\n\n"
            "Note: Cleaning (removal of dead bed bugs) is not included."
        ),
        "bbfaq_warranty": (
            # Updated warranty text:
            "Four Solutions offers 100% warranty coverage on all fully treated areas, supported by our 100% money-back guarantee.\n\n"
            "Important Note: If you choose partial treatment (e.g., treating only one bedroom despite our recommendation for additional rooms), "
            "full warranty coverage may not apply due to the risk of bed bugs reinfesting from untreated areas.\n\n"
            "Our Warranty Includes:\n\n"
            "1) Unlimited re-treatments of the treated areas.\n"
            "2) Coverage lasting 6 months from the initial treatment date.\n"
            "3) A 100% money-back guarantee if bed bugs persist after 4 treatment attempts, provided proof of infestation is given.\n\n"
            "Additional Conditions:\n\n"
            "If you opt to claim the 100% money-back guarantee, the unlimited re-treatment option will no longer apply.\n"
            "If after 4 treatments you prefer additional treatments instead of claiming the money-back guarantee, "
            "you will no longer be eligible for the money-back option.\n\n"
            "Four Solutions is committed to providing Singapore’s most competitive bed bug warranty, ensuring your peace of mind."
        ),
        "bbfaq_preparation": (
            "Preparation\n"
            "What should I prepare before the appointment?\n\n"
            "To ensure a smooth and effective bed bug treatment, please follow these preparation steps before our technician arrives:\n\n"
            "1) Clearly note down locations where you've spotted bed bugs, including an approximate count. "
            "Please share these details with our technician upon arrival.\n\n"
            "2) Safely remove items sensitive to heat from treatment areas, including creams, lotions, cosmetics, "
            "wax products, candles, food items, and sensitive artworks or paintings.\n"
            "(Note: We are not responsible for damage to items left in the treatment area.)\n\n"
            "3) Unplug and remove electronic appliances from the treatment areas, as our technician will need clear access.\n\n"
            "4) Minimize the number of occupants in the house during the treatment period to ensure safety and comfort.\n\n"
            "5) Ensure the treatment spaces are clutter-free, allowing enough room for our equipment and technician to work effectively.\n\n"
            "Arrival Note:\n"
            "We aim to arrive within 1 hour of the scheduled appointment time. Should there be any delays, we will notify you promptly."
        ),
        "bbfaq_payment": (
            "We accept the following payment methods:\n\n"
            "* PayNow: Payment via UEN: 201812722M\n"
            "* Atome: Interest-free installment for 3 months (5% surcharge applies)\n"
            "* Cash: Please inform us in advance if you need to pay in cash and prepare the exact amount."
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
    send_message(payload, phone_number_id, access_token, f"Sent Bedbug FAQ Answer ({faq_id})")

# ------------------------------
# Optional: Entry Point for the Bedbug Flow
# ------------------------------
def run_flow(to, phone_number_id, access_token, bedbug_data, send_text_message, initiate_live_agent=None, sender_name="User", send_interactive_message=None):
    """
    Entry point for the bedbug flow.
    This function initiates the bedbug flow by sending the initial menu.
    """
    send_bedbug_initial_menu(to, phone_number_id, access_token)
    # The flow continues based on user responses handled by your dispatcher.











