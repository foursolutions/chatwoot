# flows/bedbug.py
from services.twilio_client import send_whatsapp_message
from sessions import bedbug_data

def run_flow(to):
    """
    Initiates the bedbug service quotation flow.
    """
    bedbug_data[to] = {"stage": "area_selection"}
    menu_text = (
        "🪲 *Bedbug Quotation*\n\n"
        "Reply with the number corresponding to the affected area:\n"
        "1. Bedroom\n"
        "2. Living Area\n"
        "3. Whole Unit\n"
        "4. Commercial Space\n"
        "5. Others (Please specify)"
    )
    send_whatsapp_message(to, menu_text)

def handle_response(to, text):
    """
    Handles responses based on user's current stage in the flow.
    """
    state = bedbug_data.get(to, {})

    if state.get("stage") == "area_selection":
        area_mapping = {
            "1": "Bedroom",
            "2": "Living Area",
            "3": "Whole Unit",
            "4": "Commercial Space"
        }

        area = area_mapping.get(text.strip())
        
        if area:
            state["area"] = area
            state["stage"] = "count_entry"
            send_whatsapp_message(to, f"✅ Area selected: {area}.\n\nPlease enter an approximate number of bedbugs seen:")
        elif text.strip() == "5":
            state["stage"] = "custom_area_entry"
            send_whatsapp_message(to, "Please specify the affected area clearly:")
        else:
            send_whatsapp_message(to, "⚠️ Invalid choice, please reply with numbers 1 to 5.")

    elif state.get("stage") == "custom_area_entry":
        state["area"] = text.strip()
        state["stage"] = "count_entry"
        send_whatsapp_message(to, f"✅ Area noted: {state['area']}.\n\nNow, please enter an approximate number of bedbugs seen:")

    elif state.get("stage") == "count_entry":
        state["count"] = text.strip()
        state["stage"] = "confirmation"
        summary = (
            f"📝 *Bedbug Issue Summary*\n\n"
            f"Affected Area: {state['area']}\n"
            f"Bedbug Count: {state['count']}\n\n"
            "Reply 'confirm' to submit or 'restart' to start over."
        )
        send_whatsapp_message(to, summary)

    elif state.get("stage") == "confirmation":
        if text.strip().lower() == "confirm":
            send_whatsapp_message(
                to,
                "🎉 Thank you! We've received your details. Our team will reach out shortly with your quotation and further assistance."
            )
            bedbug_data.pop(to, None)  # Clear the session data
        elif text.strip().lower() == "restart":
            run_flow(to)
        else:
            send_whatsapp_message(to, "⚠️ Invalid response. Please reply 'confirm' or 'restart'.")

    else:
        send_whatsapp_message(to, "🤖 I didn't quite understand that. Let's start again.")
        run_flow(to)
