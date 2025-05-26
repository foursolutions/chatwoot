import requests

# ------------------------------
# WhatsApp Send Message Helper
# ------------------------------
def send_message(payload, phone_number_id, access_token, log_msg="Sent Message"):
    """
    Helper to send a message via WhatsApp API (Meta/360dialog).
    """
    url = f"https://waba.360dialog.io/v1/messages"
    headers = {"D360-API-KEY": access_token, "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(f"✅ {log_msg}:", response.json())

# ------------------------------
# Car Fumigation Flow Functions
# ------------------------------
def send_pest_control_dropdown(to, phone_number_id, access_token):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Pest Control Services"},
            "body": {"text": "Please select the pest control service you need assistance with:"},
            "footer": {"text": "Tap below to choose"},
            "action": {
                "button": "Select Service",
                "sections": [{
                    "title": "Common Pest Issues",
                    "rows": [
                        {"id": "car_fumigation", "title": "Car Fumigation 🚗", "description": "On-site fumigation & fogging"},
                        {"id": "bed_bugs", "title": "Bed Bugs 🛏️", "description": "Elimination of bed bugs"},
                        {"id": "booklice", "title": "Booklice 📚", "description": "Treatment for booklice"},
                        {"id": "cockroaches", "title": "Roaches & Ants 🐜", "description": "General pest control"},
                        {"id": "bees_wasps", "title": "Bees/Wasps 🐝", "description": "Removal of nests"},
                        {"id": "commercial_pest", "title": "Commercial Pest 🏢", "description": "Services for offices"},
                        {"id": "other_pests", "title": "Other Pest Issues 🕷️", "description": "Other pest problems"}
                    ]
                }]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Pest Control Dropdown")

def send_car_fumigation_options(to, phone_number_id, access_token):
    text = (
        "We are happy to help with your car fumigation issue!\n"
        "Select an option below for us to better understand your needs."
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
                    {"type": "reply", "reply": {"id": "car_fum_quote", "title": "Request a Quotation"}},
                    {"type": "reply", "reply": {"id": "fumigation_faq", "title": "More Info on Service"}},
                    {"type": "reply", "reply": {"id": "return_main_menu", "title": "Return to Main Menu"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Car Fumigation Options")

def send_car_fumigation_followup(to, phone_number_id, access_token):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "What pest did you see?"},
            "body": {"text": "Select from the options below:"},
            "footer": {"text": "Select Pest"},
            "action": {
                "button": "Select Pest",
                "sections": [{
                    "title": "Pest Options",
                    "rows": [
                        {"id": "car_fumigation_cockroach", "title": "Cockroaches", "description": "Cockroaches infestation in vehicle"},
                        {"id": "car_fumigation_ants", "title": "Ants", "description": "Ants infestation in vehicle"},
                        {"id": "car_fumigation_lizards", "title": "Lizards", "description": "Presence of lizards in vehicle."},
                        {"id": "car_fumigation_multiple", "title": "Multiple Pest", "description": "Multiple pest issues in vehicle"},
                        {"id": "car_fumigation_others", "title": "Others", "description": "Other pest that is not listed in the above options"}
                    ]
                }]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Car Fumigation Followup")

def process_car_fumigation_pest(to, pest_id, car_fumigation_data, phone_number_id, access_token):
    car_fumigation_data.setdefault(to, {})["pest"] = pest_id
    send_vehicle_model_selection(to, phone_number_id, access_token)

def send_vehicle_model_selection(to, phone_number_id, access_token):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Vehicle Model Type"},
            "body": {"text": "Please select your vehicle model type:"},
            "footer": {"text": "Tap below to choose"},
            "action": {
                "button": "Select Model",
                "sections": [{
                    "title": "Vehicle Types",
                    "rows": [
                        {"id": "vehicle_sedan", "title": "Sedan/Hatchback", "description": "Standard cars"},
                        {"id": "vehicle_suv", "title": "SUV", "description": "Sport Utility Vehicle"},
                        {"id": "vehicle_mpv", "title": "MPV", "description": "Multi-Purpose Vehicle"},
                        {"id": "vehicle_vans", "title": "Vans/Lorries", "description": "Commercial vehicles"},
                        {"id": "vehicle_ultra_luxury", "title": "Ultra Luxury/Super", "description": "e.g. Bentley, Ferrari, Lamborghini equivalent"},
                        {"id": "vehicle_others", "title": "Others", "description": "Other vehicle types"}
                    ]
                }]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Vehicle Model Selection")

def process_vehicle_model_selection(to, model_id, car_fumigation_data, phone_number_id, access_token):
    car_fumigation_data.setdefault(to, {})["vehicle"] = model_id
    if model_id in ["vehicle_others", "vehicle_ultra_luxury"]:
        car_fumigation_data[to]["manual_quote"] = True
        prompt_text = (
            "Please enter your vehicle model details:" 
            if model_id == "vehicle_others" 
            else "Please enter your vehicle model details for Ultra Luxury/Super:"
        )
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": prompt_text}
        }
        send_message(payload, phone_number_id, access_token, "Prompted for vehicle model details")
        car_fumigation_data[to]["awaiting_vehicle_model_details"] = True
    else:
        send_luxury_prompt(to, phone_number_id, access_token)

def send_luxury_prompt(to, phone_number_id, access_token):
    text = (
        "Does your vehicle manufacturer fall under one of the options below?\n\n"
        "1) Mercedes‑Benz\n"
        "2) BMW\n"
        "3) Audi\n"
        "4) Lexus\n"
        "5) Porsche\n"
        "6) Jaguar\n"
        "7) Tesla\n"
        "8) Range Rover\n\n"
        "These vehicle brands require additional care while servicing.\n"
        "Please select either Yes or No."
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
                    {"type": "reply", "reply": {"id": "luxury_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "luxury_no", "title": "No"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Luxury Prompt")

def send_location_selection(to, phone_number_id, access_token):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "On-Site Location Selection"},
            "body": {"text": "Please select the location nearest to the address where your vehicle will be parked:"},
            "footer": {"text": "Tap below to choose"},
            "action": {
                "button": "Select Location",
                "sections": [{
                    "title": "Locations",
                    "rows": [
                        {"id": "location_north", "title": "North", "description": "Woodlands, Yishun, Sembawang, etc"},
                        {"id": "location_northeast", "title": "North-East", "description": "Hougang, Sengkang, Punggol, etc."},
                        {"id": "location_central", "title": "Central", "description": "Orchard, Newton, River Valley, etc."},
                        {"id": "location_east", "title": "East", "description": "Bedok, Changi, Tampines, etc."},
                        {"id": "location_west", "title": "West", "description": "Jurong, Clementi, Bukit Batok, etc."},
                        {"id": "location_south", "title": "South", "description": "Bukit Merah, Bukit Timah, Queenstown"},
                        {"id": "location_sentosa", "title": "Sentosa & Restricted", "description": "Sentosa & restricted areas (clearance req'd)"}
                    ]
                }]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Location Selection")

def send_quote_summary(to, car_fumigation_data, phone_number_id, access_token):
    data = car_fumigation_data.get(to, {})
    if data.get("manual_quote"):
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Below is the estimated breakdown of your quotation:\n\n"
            "- Car Model Type Pricing: Customized Quote Required\n"
            "- Additional Care Fee: $0\n"
            "- On-site Service Charge: $0\n\n"
            "Estimated Total: Your vehicle or service request requires a customized quotation. Please allow an agent to assist you with this.\n\n"
            "Please select an option below:"
        )
    else:
        vehicle = data.get("vehicle")
        if vehicle == "vehicle_sedan":
            base_quote = 140
        elif vehicle == "vehicle_suv":
            base_quote = 150
        elif vehicle == "vehicle_mpv":
            base_quote = 160
        elif vehicle == "vehicle_vans":
            base_quote = 170
        else:
            base_quote = 140
        additional_fee = 10 if data.get("continental") == "luxury_yes" else 0
        if data.get("location") in ["location_north", "location_northeast", "location_east"]:
            location_charge = 20
        elif data.get("location") in ["location_central", "location_west", "location_south"]:
            location_charge = 25
        elif data.get("location") in ["location_others", "location_sentosa"]:
            location_charge = 40
        else:
            location_charge = 0
        computed_quote = base_quote + additional_fee + location_charge
        car_fumigation_data[to]["computed_quote"] = computed_quote
        additional_fee_str = f"${additional_fee}" if additional_fee != 0 else "$0"
        summary_text = (
            "On-Site Car Fumigation Quotation\n\n"
            "Below is the estimated breakdown of your quotation:\n\n"
            f"- Car Model Type Pricing: ${base_quote}\n"
            f"- Additional Care Fee: {additional_fee_str}\n"
            f"- On-site Service Charge: ${location_charge}\n\n"
            f"Estimated Total: ${computed_quote}\n\n"
            "Please select an option below:"
        )
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": summary_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "book_appointment", "title": "Book Now"}},
                    {"type": "reply", "reply": {"id": "fumigation_faq", "title": "More Info on Service"}},
                    {"type": "reply", "reply": {"id": "return_main_menu", "title": "Return to Main Menu"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Quote Summary")

def send_appointment_method_prompt(to, phone_number_id, access_token):
    text = (
        "How would you like to set your appointment?\n\n"
        "Tap 'ASAP' if you'd like to book immediately, or 'Enter Date/Time' to specify a date/time."
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
                    {"type": "reply", "reply": {"id": "apt_asap", "title": "ASAP"}},
                    {"type": "reply", "reply": {"id": "apt_enter_datetime", "title": "Enter Date/Time"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Appointment Method Prompt")

def send_appointment_summary(to, car_fumigation_data, phone_number_id, access_token, send_text_message):
    data = car_fumigation_data.get(to, {})
    if data.get("manual_quote"):
        computed_quote = "Manual Quotation"
    else:
        vehicle = data.get("vehicle")
        if vehicle == "vehicle_sedan":
            base_quote = 140
        elif vehicle == "vehicle_suv":
            base_quote = 150
        elif vehicle == "vehicle_mpv":
            base_quote = 160
        elif vehicle == "vehicle_vans":
            base_quote = 170
        else:
            base_quote = 140
        additional_charge = 10 if data.get("continental") == "luxury_yes" else 0
        if data.get("location") in ["location_north", "location_northeast", "location_east"]:
            location_charge = 20
        elif data.get("location") in ["location_central", "location_west", "location_south"]:
            location_charge = 25
        elif data.get("location") in ["location_others", "location_sentosa"]:
            location_charge = 40
        else:
            location_charge = 0
        computed_quote = base_quote + additional_charge + location_charge
        car_fumigation_data[to]["computed_quote"] = computed_quote

    appointment_datetime = data.get("appointment_datetime", "Not provided")
    parking_address = data.get("parking_address", "Not provided")
    vehicle_number = data.get("vehicle_number", "Not provided")
    pest_reported_id = data.get("pest", "Not provided")
    pest_mapping = {
        "car_fumigation_cockroach": "Cockroaches",
        "car_fumigation_ants": "Ants",
        "car_fumigation_lizards": "Lizards",
        "car_fumigation_multiple": "Multiple Pest",
        "car_fumigation_others": "Others"
    }
    pest_reported = pest_mapping.get(pest_reported_id, pest_reported_id)

    summary_text = (
        "Please confirm your appointment details:\n\n"
        "Below is the breakdown for your onsite car fumigation quote:\n"
        f"Your estimated total is: ${computed_quote}\n\n"
        f"Pest Reported: {pest_reported}\n"
        f"Preferred Date & Time: {appointment_datetime}\n"
        f"Parking Address: {parking_address}\n"
        f"Vehicle Number: {vehicle_number}\n\n"
        "Select 'Yes' to proceed or 'No' to return to car fumigation quote details."
    )

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": summary_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "confirm_apt_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "confirm_apt_no", "title": "No"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Appointment Confirmation")

def handle_appointment_datetime(to, text_body, car_fumigation_data, send_text_message):
    car_fumigation_data[to]["appointment_datetime"] = text_body
    car_fumigation_data[to].pop("awaiting_appointment_datetime", None)
    send_text_message(to, "Please provide your full parking address (where the vehicle will be).")
    car_fumigation_data[to]["awaiting_parking_address"] = True

def handle_parking_address(to, text_body, car_fumigation_data, send_text_message):
    car_fumigation_data[to]["parking_address"] = text_body
    car_fumigation_data[to].pop("awaiting_parking_address", None)
    send_text_message(to, "Please provide your vehicle number.")
    car_fumigation_data[to]["awaiting_vehicle_number"] = True

def handle_vehicle_number(to, text_body, car_fumigation_data, send_text_message, phone_number_id, access_token):
    car_fumigation_data[to]["vehicle_number"] = text_body
    car_fumigation_data[to].pop("awaiting_vehicle_number", None)
    send_appointment_summary(to, car_fumigation_data, phone_number_id, access_token, send_text_message)

def send_quote_options(to, phone_number_id, access_token):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Please select an option to proceed:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "book_appointment", "title": "Book Now"}},
                    {"type": "reply", "reply": {"id": "fumigation_faq", "title": "More Info on Service"}},
                    {"type": "reply", "reply": {"id": "return_main_menu", "title": "Return to Main Menu"}}
                ]
            }
        }
    }
    send_message(payload, phone_number_id, access_token, "Sent Quote Options")

def send_car_fumigation_faq(to, phone_number_id, access_token, send_interactive_message):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Car Fumigation FAQ"},
            "body": {"text": "Select a FAQ question:"},
            "footer": {"text": "Tap an option"},
            "action": {
                "button": "Select FAQ",
                "sections": [{
                    "title": "FAQ Questions",
                    "rows": [
                        {"id": "cfq_safe", "title": "Is it safe? Kids/Pets", "description": "Safety with HACCP chemicals"},
                        {"id": "cfq_included", "title": "Service Details", "description": "What's included in our service?"},
                        {"id": "cfq_warranty", "title": "Our Warranty", "description": "Warranty information"},
                        {"id": "cfq_preparation", "title": "Preparation", "description": "What to prepare before service"},
                        {"id": "cfq_duration", "title": "Service Duration", "description": "How long the service takes"},
                        {"id": "cfq_payment", "title": "Payment Options", "description": "Payment methods accepted"}
                    ]
                }]
            }
        }
    }
    send_interactive_message(to, payload)

def process_car_fumigation_faq_response(to, faq_id, phone_number_id, access_token):
    faq_answers = {
        "cfq_safe": (
            "Our car fumigation service ensures safety for your children and pets through:\n"
            "• NEA HACCP-certified chemicals, safe even for Food & Beverage environments.\n"
            "• Non-oily solutions, reducing chemical residues.\n"
            "• Completely odorless treatment.\n"
            "• Professional fogging equipment, avoiding aerosol residues from off-the-shelf products."
        ),
        "cfq_included": (
            "Our car fumigation service includes:\n"
            "• Odorless, non-oily, HACCP-grade chemical application.\n"
            "• Professional fogging machinery.\n"
            "• Complete interior disinfecting wipe-down.\n"
            "• Vacuuming to remove all dead pests.\n"
            "• Application of a residual protective coating lasting up to 3 months."
        ),
        "cfq_warranty": (
            "Warranty eligibility is assessed by our on-site technician post-service, provided no cockroaches are found after treatment.\n"
            "Warranty terms:\n"
            "• Effective from 1 week after initial servicing, lasting an additional 3 weeks (total 1-month coverage).\n"
            "• One-time complimentary car fumigation at the original service location.\n"
            "Please allow 7-14 working days for warranty appointment scheduling; earlier slots may be available."
        ),
        "cfq_preparation": (
            "Please follow these preparation steps:\n"
            "* Remove personal items including baby seats, perfume, sunglasses, tissues, pillows, soft toys, valuables, and food items.\n"
            "* Completely empty the car boot for effective treatment.\n"
            "* Park your car in a location that allows easy access for our technician.\n"
            "* Provide space for our technician to safely set up equipment and perform the service.\n"
            "* You will receive notifications before arrival and completion.\n"
            "* Inform us at least 2 hours before the appointment if you need to reschedule.\n"
            "A clutter-free car enhances the effectiveness of our service."
        ),
        "cfq_duration": (
            "Our car fumigation typically takes between 1.5 to 2 hours, though it may vary depending on the situation.\n"
            "You can continue with your daily activities as your presence is not required during the entire process."
        ),
        "cfq_payment": (
            "We accept the following payment methods:\n"
            "* PayNow: Payment via UEN: 201812722M\n"
            "* Atome: Interest-free installment payments (3 months) with a 5% surcharge.\n"
            "* Cash: Please inform us if you prefer cash and prepare the exact amount."
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
    send_message(payload, phone_number_id, access_token, "Sent Car Fumigation FAQ Answer")

def send_car_fumigation_preparation(to, phone_number_id, access_token):
    prep_text = (
        "Please follow these preparation steps:\n"
        "* Remove personal items including baby seats, perfume, sunglasses, tissues, pillows, soft toys, valuables, and food items.\n"
        "* Completely empty the car boot for effective treatment.\n"
        "* Park your car in a location that allows easy access for our technician.\n"
        "* Provide space for our technician to safely set up equipment and perform the service.\n"
        "* You will receive notifications before our arrival and completion.\n"
        "* Inform us at least 2 hours prior if you need to reschedule.\n"
        "A clutter-free car enhances the effectiveness of our service."
    )
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": prep_text}
    }
    send_message(payload, phone_number_id, access_token, "Sent Car Fumigation Preparation")

def compute_and_send_quote(to, car_fumigation_data, phone_number_id, access_token, send_text_message):
    """
    After selecting on-site location, computes and sends the quote summary.
    """
    send_quote_summary(to, car_fumigation_data, phone_number_id, access_token)

# ------------------------------
# Optional: Entry Point for the Flow
# ------------------------------
def run_flow(to, phone_number_id, access_token, car_fumigation_data, send_text_message, send_interactive_message):
    """
    Entry point for the car fumigation flow.
    """
    send_pest_control_dropdown(to, phone_number_id, access_token)
    # The flow continues based on interactive responses handled by your dispatcher.
