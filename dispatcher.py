# dispatcher.py

import os
import json
import redis

import flows.car_fumigation as cf
import flows.bedbug as bb

# -------------------------------
# REDIS SETUP
# -------------------------------
# If you have a REDIS_URL environment variable, it will use that.
# Otherwise it falls back to a hard-coded URI (replace with your own if needed).
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://:wD!a4yZ4NFCCtBr@redis-14395.c321.us-east-1-2.ec2.redns.redis-cloud.com:14395"
)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

# Prefix used so we can manage per-user state under "carfum:<user>"
FLOW = "carfum"


def get_user_state(user_id):
    """
    Retrieve the JSON-encoded state for a given user_id from Redis.
    If nothing is stored yet, returns an empty dict.
    """
    key = f"{FLOW}:{user_id}"
    raw = r.get(key)
    if not raw:
        return {}
    return json.loads(raw)


def set_user_state(user_id, state):
    """
    Overwrite the stored state for user_id with this dict, expiring after 1 hour.
    """
    key = f"{FLOW}:{user_id}"
    r.set(key, json.dumps(state), ex=3600)


def clear_user_state(user_id):
    """
    Remove any existing state for this user_id.
    """
    key = f"{FLOW}:{user_id}"
    r.delete(key)


# -------------------------------
# DISPATCHER ENTRYPOINT
# -------------------------------
def handle_message(
    sender_number,
    message_text,
    button_reply=None,
    list_reply=None,
    access_token=None,
    phone_number_id=None,
    send_text_message=None,
    send_interactive_message=None
):
    """
    Redis-backed state machine for Pest Control flows (Car Fumigation + Bed Bugs).

    Arguments:
      - sender_number: the user's WhatsApp phone number (e.g. "+6581234567")
      - message_text: any free-text they typed (used to reset to main menu if they typed "menu")
      - button_reply: the exact "text" of the button they tapped (e.g. "Book Now")
      - list_reply: the exact "title" of the list row they tapped (e.g. "Cockroaches")
      - access_token: your 360dialog API Key (string)
      - phone_number_id: your 360dialog Phone Number ID (string)
      - send_text_message: callback function with signature send_text_message(to, body)
      - send_interactive_message: callback function with signature send_interactive_message(to, payload)

    This function will:
      1. Check Redis for the user's current "step".
      2. Based on that step + the incoming interactive response (button or list), advance the flow.
      3. Call the appropriate cf.* (Car Fumigation) or bb.* (Bed Bugs) helper.
      4. Update Redis to the next step.
    """

    user_id = sender_number
    state = get_user_state(user_id)
    step = state.get("step")

    # --- SPECIAL CASE: If the user typed "menu", "main menu", or "restart", show the pest dropdown again. ---
    if message_text and message_text.lower() in ("menu", "main menu", "restart"):
        clear_user_state(user_id)
        # Step back to "select_service" so that next interactive tap must choose Car Fumigation / Bed Bugs, etc.
        cf.send_pest_control_dropdown(user_id, phone_number_id, access_token)
        set_user_state(user_id, {"step": "select_service"})
        return

    # --- STEP 0: After “Need help on Pest!” the user must choose a category (Car Fumigation, Bed Bugs, etc.) ---
    if step == "select_service" and list_reply:
        # Car Fumigation chosen?
        if list_reply.startswith("Car Fumigation"):
            state["step"] = "cf_main"
            set_user_state(user_id, state)
            cf.send_car_fumigation_options(user_id, phone_number_id, access_token)
            return

        # Bed Bugs chosen?
        if list_reply.startswith("Bed Bugs"):
            state["step"] = "bb_start"
            set_user_state(user_id, state)
            bb.send_bedbug_initial_menu(user_id, phone_number_id, access_token)
            return

        # If unrecognized, just re-show the pest dropdown
        cf.send_pest_control_dropdown(user_id, phone_number_id, access_token)
        return

    # --- STEP 1: Car Fumigation main menu (after “Car Fumigation 🚗”) ---
    if step == "cf_main" and button_reply:
        # “Request a Quotation”
        if button_reply == "Request a Quotation":
            state["step"] = "cf_awaiting_pest"
            set_user_state(user_id, state)
            cf.send_car_fumigation_followup(user_id, phone_number_id, access_token)
            return

        # “More Info on Service”
        if button_reply == "More Info on Service":
            # We need to send the interactive FAQ list. The helper signature is:
            #   cf.send_car_fumigation_faq(to, phone_number_id, access_token, send_interactive_message)
            cf.send_car_fumigation_faq(user_id, phone_number_id, access_token, send_interactive_message)
            return

        # “Return to Main Menu”
        if button_reply == "Return to Main Menu":
            clear_user_state(user_id)
            cf.send_pest_control_dropdown(user_id, phone_number_id, access_token)
            set_user_state(user_id, {"step": "select_service"})
            return

    # --- STEP 2: After tapping “Request a Quotation”, user must select which pest they saw in the car. ---
    if step == "cf_awaiting_pest" and list_reply:
        # The list IDs look like "car_fumigation_cockroach", "car_fumigation_ants", etc.
        # We call process_car_fumigation_pest(to, pest_id, car_fumigation_data, phone_number_id, access_token).
        # Here we pass a fresh data dict. In a production version, you'd read/write from a per-user store.
        cf_data = {}
        cf.process_car_fumigation_pest(user_id, list_reply, cf_data, phone_number_id, access_token)
        # The above helper will immediately call send_vehicle_model_selection(...)
        state["step"] = "cf_awaiting_model"
        set_user_state(user_id, state)
        return

    # --- STEP 3: After selecting a pest, user must pick their vehicle model. ---
    if step == "cf_awaiting_model" and list_reply:
        cf_data = {}
        cf.process_vehicle_model_selection(user_id, list_reply, cf_data, phone_number_id, access_token)
        # process_vehicle_model_selection either asks for manual model details (if “Other/Ultra Luxury”) or jumps to send_luxury_prompt(...)
        state["step"] = "cf_awaiting_luxury"
        set_user_state(user_id, state)
        return

    # --- STEP 4: After send_luxury_prompt (Yes/No), user picks “Yes” or “No”. ---
    if step == "cf_awaiting_luxury" and button_reply in ("Yes", "No"):
        # We store “luxury_yes” or “luxury_no” so that the quote calculation can include extra fees if needed.
        luxury_id = "luxury_yes" if button_reply == "Yes" else "luxury_no"
        cf_data = {user_id: {"continental": luxury_id}}
        # Now we prompt for location
        cf.send_location_selection(user_id, phone_number_id, access_token)
        state["step"] = "cf_awaiting_location"
        set_user_state(user_id, state)
        return

    # --- STEP 5: After choosing location (a list_reply like “location_north”), compute & send the quote summary. ---
    if step == "cf_awaiting_location" and list_reply:
        cf_data = {user_id: {"location": list_reply}}
        # compute_and_send_quote( to, car_fumigation_data, phone_number_id, access_token, send_text_message )
        cf.compute_and_send_quote(
            user_id,
            cf_data,
            phone_number_id,
            access_token,
            send_text_message
        )
        state["step"] = "cf_showing_summary"
        set_user_state(user_id, state)
        return

    # --- STEP 6: After showing quote summary, user taps either “Book Now”, “More Info on Service”, or “Return to Main Menu”. ---
    if step == "cf_showing_summary" and button_reply:
        if button_reply == "Book Now":
            state["step"] = "cf_appointment_method"
            set_user_state(user_id, state)
            cf.send_appointment_method_prompt(user_id, phone_number_id, access_token)
            return

        if button_reply == "More Info on Service":
            cf.send_quote_options(user_id, phone_number_id, access_token)
            return

        if button_reply == "Return to Main Menu":
            clear_user_state(user_id)
            cf.send_pest_control_dropdown(user_id, phone_number_id, access_token)
            set_user_state(user_id, {"step": "select_service"})
            return

    # --- STEP 7: After tapping “Book Now”, user picks “ASAP” or “Enter Date/Time”. ---
    if step == "cf_appointment_method" and button_reply in ("ASAP", "Enter Date/Time"):
        if button_reply == "ASAP":
            send_text_message(user_id, "Please provide your full parking address (where the vehicle will be).")
            # In the real flow, you would now set a flag to await_parking_address = True
        else:
            send_text_message(user_id, "Please enter your preferred date and time for the appointment.")
            # In the real flow, you would now set a flag to await_appointment_datetime = True

        state["step"] = "cf_appointment_confirmation"
        set_user_state(user_id, state)
        return

    # --- STEP 8: After collecting date/time or address, user confirms “Yes” or “No”. ---
    if step == "cf_appointment_confirmation" and button_reply in ("Yes", "No"):
        if button_reply == "Yes":
            cf.send_car_fumigation_preparation(user_id, phone_number_id, access_token)
        else:
            # If they say “No”, go back to showing the quote summary again
            state["step"] = "cf_showing_summary"
            set_user_state(user_id, state)
            cf.send_quote_options(user_id, phone_number_id, access_token)
        return

    # === BEDBUG FLOW (example stub) ===
    if step == "bb_start" and list_reply:
        # In a full Bed Bug flow, you would handle that here.
        # For now, we simply re-display the main pest dropdown when Bed Bugs is tapped:
        cf.send_pest_control_dropdown(user_id, phone_number_id, access_token)
        set_user_state(user_id, {"step": "select_service"})
        return

    # --- FALLBACK: if nothing matched, re-show the pest dropdown ---
    cf.send_pest_control_dropdown(user_id, phone_number_id, access_token)
    set_user_state(user_id, {"step": "select_service"})
