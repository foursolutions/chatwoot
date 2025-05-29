import requests

# ====== CONFIGURATION ======
NAMESPACE = "94d66366_9ec1_43a3_a84c_46039bd33ef5"

# Helper for sending WhatsApp message templates via 360dialog v2 API
def send_template_message(to, template_name, namespace, variables, access_token):
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": access_token,
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "namespace": namespace,
            "language": {
                "policy": "deterministic",
                "code": "en"
            },
            "name": template_name,
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(var)} for var in variables]
                }
            ]
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"✅ Sent WhatsApp Template '{template_name}' to {to}: {response.text}")

# Helper for sending regular WhatsApp interactive/list messages (not templates)
def send_interactive_message(to, payload, access_token):
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": access_token,
        "Content-Type": "application/json"
    }
    payload["to"] = to
    payload["messaging_product"] = "whatsapp"
    response = requests.post(url, json=payload, headers=headers)
    print(f"✅ Sent Interactive Message to {to}: {response.text}")

# =========================== CAR FUMIGATION FLOW ===========================

# --- Template screens ---

def send_car_fum_menu(to, access_token):
    send_template_message(
        to=to,
        template_name="car_fum_menu",
        namespace=NAMESPACE,
        variables=[],
        access_token=access_token
    )

def send_quote_summary(to, model_price, extra_fee, service_fee, total, access_token):
    send_template_message(
        to=to,
        template_name="car_fum_quote_summary",
        namespace=NAMESPACE,
        variables=[model_price, extra_fee, service_fee, total],
        access_token=access_token
    )

def send_appointment_method(to, access_token):
    send_template_message(
        to=to,
        template_name="car_fum_appointment_method",
        namespace=NAMESPACE,
        variables=[],
        access_token=access_token
    )

def send_appointment_confirmation(to, total, pest, date_time, address, vehicle_no, access_token):
    send_template_message(
        to=to,
        template_name="car_fum_appointment_confirmation",
        namespace=NAMESPACE,
        variables=[total, pest, date_time, address, vehicle_no],
        access_token=access_token
    )

def send_quote_options(to, access_token):
    send_template_message(
        to=to,
        template_name="car_fum_quote_options",
        namespace=NAMESPACE,
        variables=[],
        access_token=access_token
    )

# --- Classic lists (keep using interactive since templates don't support lists) ---

def send_pest_list(to, access_token):
    payload = {
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
                        {"id": "pest_cockroach", "title": "Cockroaches", "description": "Cockroaches infestation in vehicle"},
                        {"id": "pest_ants", "title": "Ants", "description": "Ants infestation in vehicle"},
                        {"id": "pest_lizards", "title": "Lizards", "description": "Presence of lizards in vehicle"},
                        {"id": "pest_multiple", "title": "Multiple Pest", "description": "Multiple pest issues in vehicle"},
                        {"id": "pest_others", "title": "Others", "description": "Other pest that is not listed in the above options"}
                    ]
                }]
            }
        }
    }
    send_interactive_message(to, payload, access_token)

def send_vehicle_model_list(to, access_token):
    payload = {
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
                        {"id": "model_sedan", "title": "Sedan/Hatchback"},
                        {"id": "model_suv", "title": "SUV"},
                        {"id": "model_mpv", "title": "MPV"},
                        {"id": "model_van", "title": "Vans/Lorries"},
                        {"id": "model_ultra", "title": "Ultra Luxury/Super"},
                        {"id": "model_others", "title": "Others"}
                    ]
                }]
            }
        }
    }
    send_interactive_message(to, payload, access_token)

def send_location_list(to, access_token):
    payload = {
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
                        {"id": "loc_north", "title": "North"},
                        {"id": "loc_northeast", "title": "North-East"},
                        {"id": "loc_central", "title": "Central"},
                        {"id": "loc_east", "title": "East"},
                        {"id": "loc_west", "title": "West"},
                        {"id": "loc_south", "title": "South"},
                        {"id": "loc_sentosa", "title": "Sentosa & Restricted"},
                    ]
                }]
            }
        }
    }
    send_interactive_message(to, payload, access_token)

def send_luxury_prompt(to, access_token):
    payload = {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
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
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "luxury_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "luxury_no", "title": "No"}}
                ]
            }
        }
    }
    send_interactive_message(to, payload, access_token)

# --- (Add your flow logic, dispatcher, and data storage as needed) ---

# Example usage:
# send_car_fum_menu(user_phone, ACCESS_TOKEN)
# send_quote_summary(user_phone, "$140", "$10", "$25", "$175", ACCESS_TOKEN)

# Plug these functions into your dispatcher/handler as needed!
