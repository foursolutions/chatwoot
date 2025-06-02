# dispatcher.py

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
from flows.bedbug import send_bedbug_initial_menu

# -------------------------------
# REDIS SETUP
# -------------------------------
# Make sure REDIS_URL is set in your .env or environment
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://:wD!a4yZ4NFCCtBr@redis-14395.c321.us-east-1-2.ec2.redns.redis-cloud.com:14395"
)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

# Prefix used so we can manage per-user state under "carfum:<user>"
FLOW = "carfum"

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

# -------------------------------
# DISPATCHER ENTRYPOINT
# -------------------------------
def handle_message(sender_number, message_text, button_reply=None, list_reply=None, access_token=None):
    """
    Redis-backed state machine for Pest Control flows (starting with Car Fumigation as an example).
    
    Parameters:
      - sender_number: the user's phone number (as string, e.g. "+6581234567")
      - message_text: raw free-text (unused except for "menu" commands)
      - button_reply: string of the button's "title" when a button was tapped
      - list_reply: string of the list row's "title" when a list item was tapped
      - access_token: your 360dialog API key, passed through from main.py
    """
    user_id = sender_number
    state   = get_user_state(FLOW, user_id)
    step    = state.get("step")

    # If user explicitly typed "menu" or "main menu", restart the pest-control dropdown
    if message_text and message_text.lower() in ("menu", "main menu", "restart"):
        clear_user_state(FLOW, user_id)
        from flows.car_fumigation import send_pest_control_dropdown
        send_pest_control_dropdown(user_id, access_token)
        set_user_state(FLOW, user_id, {"step": "select_service"})
        return

    # Step 0: User has just tapped "Need help on Pest!" → expecting one of the pest-control categories
    if step == "select_service" and list_reply:
        # Car Fumigation chosen?
        if list_reply.startswith("Car Fumigation"):
            state["step"] = "main_menu"
            set_user_state(FLOW, user_id, state)
            send_car_fum_menu(user_id, access_token)
            return

        # Bed Bugs chosen?
        if list_reply.startswith("Bed Bugs"):
            state["step"] = "bedbug_start"
            set_user_state(FLOW, user_id, state)
            send_bedbug_initial_menu(user_id, access_token)
            return

        # (Add other pest categories here, e.g. Booklice, Roaches & Ants, etc.)
        # Example:
        # if list_reply.startswith("Booklice"):
        #     from flows.booklice import send_booklice_initial_menu
        #     state["step"] = "booklice_start"
        #     set_user_state(FLOW, user_id, state)
        #     send_booklice_initial_menu(user_id, access_token)
        #     return

        # Fallback: re-show the pest-control dropdown
        from flows.car_fumigation import send_pest_control_dropdown
        send_pest_control_dropdown(user_id, access_token)
        return

    # Step 1: Car Fumigation submenu logic (after selecting Car Fumigation above)
    if step in (None, "main_menu"):
        if button_reply == "Request a Quotation":
            state["step"] = "awaiting_pest"
            set_user_state(FLOW, user_id, state)
            send_pest_list(user_id, access_token)
            return
        elif button_reply == "More Info on Service":
            send_car_fum_menu(user_id, access_token)
            return
        elif button_reply == "Return to Main Menu":
            clear_user_state(FLOW, user_id)
            from flows.car_fumigation import send_pest_control_dropdown
            send_pest_control_dropdown(user_id, access_token)
            set_user_state(FLOW, user_id, {"step": "select_service"})
            return

    # Step 2: Pest selection → list reply
    if step == "awaiting_pest" and list_reply:
        state["pest"] = list_reply
        state["step"] = "awaiting_model"
        set_user_state(FLOW, user_id, state)
        send_vehicle_model_list(user_id, access_token)
        return

    # Step 3: Vehicle model selection → list reply
    if step == "awaiting_model" and list_reply:
        state["model"] = list_reply
        state["step"] = "awaiting_location"
        set_user_state(FLOW, user_id, state)
        send_location_list(user_id, access_token)
        return

    # Step 4: Location selection → list reply
    if step == "awaiting_location" and list_reply:
        state["location"] = list_reply
        state["step"] = "awaiting_luxury"
        set_user_state(FLOW, user_id, state)
        send_luxury_prompt(user_id, access_token)
        return

    # Step 5: Luxury car prompt → button reply ("Yes"/"No")
    if step == "awaiting_luxury" and button_reply in ("Yes", "No"):
        state["luxury"] = button_reply
        # Example pricing logic
        state["model_price"] = "$150"
        state["extra_fee"]   = "$20" if button_reply == "Yes" else "$0"
        state["service_fee"] = "$30"
        total = (
            int(state["model_price"].strip("$"))
            + int(state["extra_fee"].strip("$"))
            + int(state["service_fee"].strip("$"))
        )
        state["total"] = f"${total}"
        state["step"]  = "showing_summary"
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

    # Step 6: Showing Quote Summary → button reply ("Book Now", "More Info on Service", "Return to Main Menu")
    if step == "showing_summary" and button_reply:
        if button_reply == "Book Now":
            state["step"] = "appointment_method"
            set_user_state(FLOW, user_id, state)
            send_appointment_method(user_id, access_token)
            return
        elif button_reply == "More Info on Service":
            send_quote_options(user_id, access_token)
            return
        elif button_reply == "Return to Main Menu":
            clear_user_state(FLOW, user_id)
            from flows.car_fumigation import send_pest_control_dropdown
            send_pest_control_dropdown(user_id, access_token)
            set_user_state(FLOW, user_id, {"step": "select_service"})
            return

    # Step 7: Appointment method ("ASAP" or "Enter Date/Time")
    if step == "appointment_method" and button_reply:
        if button_reply == "ASAP":
            state["date_time"] = "ASAP"
        elif button_reply == "Enter Date/Time":
            state["date_time"] = "Custom Date/Time"
        state["step"] = "appointment_confirmation"
        set_user_state(FLOW, user_id, state)

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

    # Step 8: Appointment confirmation ("Yes" / "No")
    if step == "appointment_confirmation" and button_reply in ("Yes", "No"):
        if button_reply == "Yes":
            clear_user_state(FLOW, user_id)
            send_car_fum_menu(user_id, access_token)
            set_user_state(FLOW, user_id, {"step": "main_menu"})
        else:
            state["step"] = "showing_summary"
            set_user_state(FLOW, user_id, state)
            send_quote_options(user_id, access_token)
        return

    # --- FALLBACK: unknown state → show Car Fumigation main menu again ---
    send_car_fum_menu(user_id, access_token)
    set_user_state(FLOW, user_id, {"step": "main_menu"})
