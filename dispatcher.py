import os
import json
import redis
from flows.car_fumigation import (
    send_car_fum_menu,
    send_pest_list,
    send_vehicle_model_list,
    send_location_list,
    send_luxury_prompt,
    send_quote_summary,
    send_quote_options,
    send_appointment_method,
    send_appointment_confirmation
)

# --- Redis setup ---
REDIS_URL = os.getenv("REDIS_URL") or "redis://:wD!a4yZ4NFCCtBr@redis-14395.c321.us-east-1-2.ec2.redns.redis-cloud.com:14395"
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

def get_user_state(prefix, user_id):
    key = f"{prefix}:{user_id}"
    data = r.get(key)
    return json.loads(data) if data else {}

def set_user_state(prefix, user_id, state):
    key = f"{prefix}:{user_id}"
    r.set(key, json.dumps(state), ex=3600)

def clear_user_state(prefix, user_id):
    key = f"{prefix}:{user_id}"
    r.delete(key)

# --- Constants ---
FLOW = "carfum"  # change this per flow if you have others

# --- Main dispatcher function ---
def handle_message(sender_number, message_text, button_reply=None, list_reply=None, access_token=None):
    """
    The main dispatcher to be called from your webhook.
    - sender_number: WhatsApp number of the sender
    - message_text: free text message
    - button_reply: button reply id, if any
    - list_reply: list row id, if any
    - access_token: 360dialog API token
    """
    user_id = sender_number
    state = get_user_state(FLOW, user_id)
    step = state.get("step")

    # Entry point: Main menu
    if message_text.lower() in ("menu", "main menu", "restart"):
        clear_user_state(FLOW, user_id)
        send_car_fum_menu(user_id, access_token)
        set_user_state(FLOW, user_id, {"step": "main_menu"})
        return

    # Step 1: Main menu options
    if step in (None, "main_menu"):
        # Expect a button reply
        if button_reply == "Request a Quotation":
            state["step"] = "awaiting_pest"
            set_user_state(FLOW, user_id, state)
            send_pest_list(user_id, access_token)
            return
        elif button_reply == "More Info on Service":
            # Send info message, then show options again
            # (You can create a template or just send a text message here)
            # Example placeholder:
            # send_text_message(user_id, "Our car fumigation ...")
            send_car_fum_menu(user_id, access_token)
            return
        elif button_reply == "Return to Main Menu":
            clear_user_state(FLOW, user_id)
            send_car_fum_menu(user_id, access_token)
            set_user_state(FLOW, user_id, {"step": "main_menu"})
            return

    # Step 2: Pest selection (list reply)
    if step == "awaiting_pest" and list_reply:
        state["pest"] = list_reply
        state["step"] = "awaiting_model"
        set_user_state(FLOW, user_id, state)
        send_vehicle_model_list(user_id, access_token)
        return

    # Step 3: Vehicle model selection (list reply)
    if step == "awaiting_model" and list_reply:
        state["model"] = list_reply
        state["step"] = "awaiting_location"
        set_user_state(FLOW, user_id, state)
        send_location_list(user_id, access_token)
        return

    # Step 4: Location selection (list reply)
    if step == "awaiting_location" and list_reply:
        state["location"] = list_reply
        state["step"] = "awaiting_luxury"
        set_user_state(FLOW, user_id, state)
        send_luxury_prompt(user_id, access_token)
        return

    # Step 5: Luxury car prompt (button reply)
    if step == "awaiting_luxury" and button_reply in ("Yes", "No"):
        state["luxury"] = button_reply
        # Here you would calculate price breakdown logic
        # For demo, just set dummy values:
        state["model_price"] = "$150"
        state["extra_fee"] = "$20" if button_reply == "Yes" else "$0"
        state["service_fee"] = "$30"
        total = int(state["model_price"].strip("$")) + int(state["extra_fee"].strip("$")) + int(state["service_fee"].strip("$"))
        state["total"] = f"${total}"
        state["step"] = "showing_summary"
        set_user_state(FLOW, user_id, state)
        send_quote_summary(
            user_id,
            state["model_price"],
            state["extra_fee"],
            state["service_fee"],
            state["total"],
            access_token
        )
        return

    # Step 6: Quote options (book, info, main menu)
    if step == "showing_summary" and button_reply:
        if button_reply == "Book Now":
            state["step"] = "appointment_method"
            set_user_state(FLOW, user_id, state)
            send_appointment_method(user_id, access_token)
            return
        elif button_reply == "More Info on Service":
            # send_text_message(user_id, "Service info goes here...")
            send_quote_options(user_id, access_token)
            return
        elif button_reply == "Return to Main Menu":
            clear_user_state(FLOW, user_id)
            send_car_fum_menu(user_id, access_token)
            set_user_state(FLOW, user_id, {"step": "main_menu"})
            return

    # Step 7: Appointment method
    if step == "appointment_method" and button_reply:
        if button_reply == "ASAP":
            state["date_time"] = "ASAP"
            # Collect more info as needed; for demo, we skip
        elif button_reply == "Enter Date/Time":
            # For demo, set to a placeholder (you should handle actual input)
            state["date_time"] = "Custom Date/Time"
        state["step"] = "appointment_confirmation"
        set_user_state(FLOW, user_id, state)
        # You can prompt for address/vehicle number here as a text input if needed
        send_appointment_confirmation(
            user_id,
            state.get("total", "$0"),
            state.get("pest", "N/A"),
            state.get("date_time", "N/A"),
            state.get("location", "N/A"),
            state.get("model", "N/A"),
            access_token
        )
        return

    # Step 8: Appointment confirmation
    if step == "appointment_confirmation" and button_reply in ("Yes", "No"):
        if button_reply == "Yes":
            # Confirm booking, clear state, send thank you, etc.
            # send_text_message(user_id, "Your appointment is confirmed! Thank you.")
            clear_user_state(FLOW, user_id)
            send_car_fum_menu(user_id, access_token)
        elif button_reply == "No":
            # Return to quote options
            state["step"] = "showing_summary"
            set_user_state(FLOW, user_id, state)
            send_quote_options(user_id, access_token)
        return

    # --- Fallback: always show menu if unknown state ---
    send_car_fum_menu(user_id, access_token)
    set_user_state(FLOW, user_id, {"step": "main_menu"})

# --- End of dispatcher.py ---