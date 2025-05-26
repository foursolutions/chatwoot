# flows/mold.py
from services.twilio_client import send_whatsapp_message
from sessions import mold_removal_data

def run_flow(to):
    """
    Initiates the mold removal quotation flow.
    """
    mold_removal_data[to] = {"stage": "area_selection"}
    menu_text = (
        "🍄 *Mold Removal Service*\n\n"
        "Please specify the affected area(s):\n"
        "1. Bedroom\n"
        "2. Bathroom\n"
        "3. Store Room/Yard\n"
        "4. Living Area\n"
        "5. Kitchen\n"
        "6. Furniture\n"
        "7. Entire Unit\n"
        "8. Mold Smell Only\n"
        "9. Commercial Space\n"
        "10. Others (Please specify)"
    )
    send_whatsapp_message(to, menu_text)

def handle_response(to, text):
    """
    Handles user responses based on their current flow stage.
    """
    state = mold_removal_data.get(to, {})

    if state.get("stage") == "area_selection":
        area_mapping = {
            "1": "Bedroom",
            "2": "Bathroom",
            "3": "Store Room/Yard",
            "4": "Living Area",
            "5": "Kitchen",
            "6": "Furniture",
            "7": "Entire Unit",
            "8": "Mold Smell Only",
            "9": "Commercial Space"
        }

        area = area_mapping.get(text.strip())

        if area:
            state["area"] = area
            if area in ["Bedroom", "Bathroom"]:
                state["stage"] = "count_selection"
                prompt = f"✅ {area} selected. How many {area.lower()}(s) are affected?"
                prompt += "\n(Please reply with a number, e.g., 1, 2, 3, etc.)"
                send_whatsapp_message(to, prompt)
            else:
                state["stage"] = "growth_location"
                send_growth_prompt(to)
        elif text.strip() == "10":
            state["stage"] = "custom_area_entry"
            send_whatsapp_message(to, "Please specify the affected area clearly:")
        else:
            send_whatsapp_message(to, "⚠️ Invalid choice, please reply with numbers 1 to 10.")

    elif state.get("stage") == "custom_area_entry":
        state["area"] = text.strip()
        state["stage"] = "growth_location"
        send_growth_prompt(to)

    elif state.get("stage") == "count_selection":
        if text.strip().isdigit():
            state["count"] = int(text.strip())
            state["stage"] = "growth_location"
            send_growth_prompt(to)
        else:
            send_whatsapp_message(to, "⚠️ Please enter a valid number for affected rooms.")

    elif state.get("stage") == "growth_location":
        growth_mapping = {
            "1": "Ceiling only",
            "2": "Walls only",
            "3": "Walls and ceiling",
            "4": "Others (please specify)"
        }
        growth = growth_mapping.get(text.strip())

        if growth:
            if growth == "Others (please specify)":
                state["stage"] = "custom_growth_entry"
                send_whatsapp_message(to, "Please specify the exact mold growth location clearly:")
            else:
                state["growth_location"] = growth
                state["stage"] = "confirmation"
                send_summary(to, state)
        else:
            send_whatsapp_message(to, "⚠️ Invalid choice, please reply with numbers 1 to 4.")

    elif state.get("stage") == "custom_growth_entry":
        state["growth_location"] = text.strip()
        state["stage"] = "confirmation"
        send_summary(to, state)

    elif state.get("stage") == "confirmation":
        if text.strip().lower() == "confirm":
            send_whatsapp_message(to,
                "🎉 Thank you! We've received your details.\n"
                "Our team will reach out shortly to provide your quotation and schedule an inspection."
            )
            mold_removal_data.pop(to, None)
        elif text.strip().lower() == "restart":
            run_flow(to)
        else:
            send_whatsapp_message(to, "⚠️ Invalid response. Please reply 'confirm' or 'restart'.")

    else:
        send_whatsapp_message(to, "🤖 Let's start again clearly.")
        run_flow(to)

def send_growth_prompt(to):
    """
    Prompt the user to specify mold growth location.
    """
    prompt = (
        "Please specify where mold growth is observed:\n"
        "1. Ceiling only\n"
        "2. Walls only\n"
        "3. Walls and ceiling\n"
        "4. Others (Please specify)"
    )
    send_whatsapp_message(to, prompt)

def send_summary(to, state):
    """
    Sends a summary of collected information for final confirmation.
    """
    summary = "📝 *Mold Removal Request Summary:*\n\n"
    summary += f"Affected Area: {state['area']}\n"
    
    if "count" in state:
        summary += f"Number of affected rooms: {state['count']}\n"
    
    summary += f"Mold Growth Location: {state['growth_location']}\n\n"
    summary += "Reply 'confirm' to submit or 'restart' to begin again."
    
    send_whatsapp_message(to, summary)

