# flows/car_fumigation.py
from services.twilio_client import send_whatsapp_message
from sessions import car_fumigation_data

def run_flow(to):
    """
    Initiates the car fumigation service quotation flow.
    """
    car_fumigation_data[to] = {"stage": "pest_selection"}
    menu_text = (
        "🚗 *Car Fumigation Service*\n\n"
        "Which pest(s) are troubling your vehicle?\n"
        "Reply with the corresponding number:\n"
        "1. Cockroaches\n"
        "2. Ants\n"
        "3. Lizards\n"
        "4. Multiple pests\n"
        "5. Others (Please specify)"
    )
    send_whatsapp_message(to, menu_text)

def handle_response(to, text):
    """
    Handles user responses based on their current flow stage.
    """
    state = car_fumigation_data.get(to, {})

    if state.get("stage") == "pest_selection":
        pest_mapping = {
            "1": "Cockroaches",
            "2": "Ants",
            "3": "Lizards",
            "4": "Multiple pests"
        }
        
        pest = pest_mapping.get(text.strip())

        if pest:
            state["pest"] = pest
            state["stage"] = "vehicle_type_selection"
            send_whatsapp_message(to,
                "✅ Pest selected: {}\n\n"
                "Now, what's your vehicle type?\n"
                "1. Sedan/Hatchback\n"
                "2. SUV\n"
                "3. MPV\n"
                "4. Vans/Lorries\n"
                "5. Ultra Luxury/Supercars (Ferrari, Lamborghini, etc)\n"
                "6. Others (Please specify)".format(pest)
            )
        elif text.strip() == "5":
            state["stage"] = "custom_pest_entry"
            send_whatsapp_message(to, "Please specify clearly which pest(s) you've observed in your vehicle:")
        else:
            send_whatsapp_message(to, "⚠️ Invalid choice, please reply with numbers 1 to 5.")

    elif state.get("stage") == "custom_pest_entry":
        state["pest"] = text.strip()
        state["stage"] = "vehicle_type_selection"
        send_whatsapp_message(to,
            f"✅ Pest noted: {state['pest']}\n\n"
            "Now, what's your vehicle type?\n"
            "1. Sedan/Hatchback\n"
            "2. SUV\n"
            "3. MPV\n"
            "4. Vans/Lorries\n"
            "5. Ultra Luxury/Supercars\n"
            "6. Others (Please specify)"
        )

    elif state.get("stage") == "vehicle_type_selection":
        vehicle_mapping = {
            "1": "Sedan/Hatchback",
            "2": "SUV",
            "3": "MPV",
            "4": "Vans/Lorries",
            "5": "Ultra Luxury/Supercar"
        }
        
        vehicle = vehicle_mapping.get(text.strip())
        
        if vehicle:
            state["vehicle"] = vehicle
            state["stage"] = "location_selection"
            send_whatsapp_message(to,
                "✅ Vehicle type selected: {}\n\n"
                "Next, please select your service location:\n"
                "1. North (Woodlands, Yishun, etc.)\n"
                "2. North-East (Hougang, Sengkang, etc.)\n"
                "3. Central (Orchard, Newton, etc.)\n"
                "4. East (Bedok, Changi, etc.)\n"
                "5. West (Jurong, Clementi, etc.)\n"
                "6. South (Bukit Merah, Queenstown)\n"
                "7. Sentosa & Restricted Areas\n"
                "8. Others (Please specify)".format(vehicle)
            )
        elif text.strip() == "6":
            state["stage"] = "custom_vehicle_entry"
            send_whatsapp_message(to, "Please clearly specify your vehicle type/model:")
        else:
            send_whatsapp_message(to, "⚠️ Invalid choice, please reply with numbers 1 to 6.")

    elif state.get("stage") == "custom_vehicle_entry":
        state["vehicle"] = text.strip()
        state["stage"] = "location_selection"
        send_whatsapp_message(to,
            f"✅ Vehicle type noted: {state['vehicle']}\n\n"
            "Please select your service location:\n"
            "1. North\n"
            "2. North-East\n"
            "3. Central\n"
            "4. East\n"
            "5. West\n"
            "6. South\n"
            "7. Sentosa & Restricted Areas\n"
            "8. Others (Please specify)"
        )

    elif state.get("stage") == "location_selection":
        location_mapping = {
            "1": "North",
            "2": "North-East",
            "3": "Central",
            "4": "East",
            "5": "West",
            "6": "South",
            "7": "Sentosa & Restricted Areas"
        }
        
        location = location_mapping.get(text.strip())
        
        if location:
            state["location"] = location
            state["stage"] = "confirmation"
            send_summary(to, state)
        elif text.strip() == "8":
            state["stage"] = "custom_location_entry"
            send_whatsapp_message(to, "Please specify your exact service location clearly:")
        else:
            send_whatsapp_message(to, "⚠️ Invalid choice, please reply with numbers 1 to 8.")

    elif state.get("stage") == "custom_location_entry":
        state["location"] = text.strip()
        state["stage"] = "confirmation"
        send_summary(to, state)

    elif state.get("stage") == "confirmation":
        if text.strip().lower() == "confirm":
            send_whatsapp_message(to,
                "🎉 Thank you! We've received your details.\n"
                "Our team will reach out shortly with your quotation and scheduling options."
            )
            car_fumigation_data.pop(to, None)
        elif text.strip().lower() == "restart":
            run_flow(to)
        else:
            send_whatsapp_message(to, "⚠️ Invalid response. Please reply 'confirm' or 'restart'.")

    else:
        send_whatsapp_message(to, "🤖 Let's start over clearly.")
        run_flow(to)

def send_summary(to, state):
    """
    Sends a summary of collected information for confirmation.
    """
    summary = (
        "📝 *Car Fumigation Request Summary:*\n\n"
        f"Pest: {state['pest']}\n"
        f"Vehicle Type: {state['vehicle']}\n"
        f"Service Location: {state['location']}\n\n"
        "Reply 'confirm' to submit or 'restart' to start again."
    )
    send_whatsapp_message(to, summary)
