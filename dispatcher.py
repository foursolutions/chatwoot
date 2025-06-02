# dispatcher.py

import os
import json
from flows import car_fumigation
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_interactive_message,
)

# ==========================
# Configuration & Constants
# ==========================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE")

# Prefix for Car Fumigation flow in Redis
CARFUM_PREFIX = "carfum"

# The name of our “echo” template that simply prefixes user text
ECHO_TEMPLATE = "echo_message_text"


# ===========================
# Main Webhook Event Handler
# ===========================
def handle_event(payload: dict):
    """
    Receives the entire JSON payload from Meta/360dialog, checks for WhatsApp messages,
    and passes each message to route_user().
    """
    if payload.get("object") != "whatsapp_business_account":
        return

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            val = change.get("value", {})
            messages = val.get("messages", [])
            metadata = val.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", PHONE_NUMBER_ID)

            for message in messages:
                from_number = message.get("from")  # e.g. "6591234567"
                msg_type = message.get("type")

                button_id = None
                list_id = None
                text_body = None

                # 1) Check for interactive replies first
                if msg_type == "interactive":
                    interactive = message.get("interactive", {})
                    itype = interactive.get("type")
                    if itype == "button_reply":
                        button_id = interactive["button_reply"]["id"]
                    elif itype == "list_reply":
                        list_id = interactive["list_reply"]["id"]

                # 2) Otherwise, if it's plain text:
                elif msg_type == "text":
                    text_body = message["text"]["body"].strip().lower()

                # 3) Delegate to route_user()
                route_user(
                    from_number,
                    button_id,
                    list_id,
                    text_body,
                    phone_number_id
                )


def route_user(from_number, button_id, list_id, text_body, phone_number_id):
    """
    Routes the interaction based on button_id, list_id, or text_body.
    Auto‐sends main_menu on any inbound plain text if no state exists.
    All free-text responses now use the echo_message_text template.
    """

    # 0) If user sent ANY text, and they have no saved state (or typed "menu"), send main_menu
    state = get_user_state(CARFUM_PREFIX, from_number)
    if text_body:
        if text_body == "menu" or not state:
            car_fumigation.send_main_menu(
                to=from_number,
                phone_number_id=phone_number_id
            )
            state = {"step": "sent_main_menu"}
            set_user_state(CARFUM_PREFIX, from_number, state)
            return

    # === 1) User tapped “Need help on Pest!” ===
    if button_id == "pest_control":
        car_fumigation.send_pest_control_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        state = {"step": "sent_pest_list"}
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # === 2) User selected “Car Fumigation” from that interactive list ===
    if list_id == "car_fumigation":
        car_fumigation.send_car_fum_menu(
            to=from_number,
            phone_number_id=phone_number_id
        )
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["step"] = "sent_car_fum_menu"
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # === Car Fumigation submenu buttons ===

    # 3) “Request a Quotation” (button_id="car_fum_quote")
    if button_id == "car_fum_quote":
        car_fumigation.send_pest_type_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["step"] = "awaiting_pest_type"
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # 4) “More Info on Service” (button_id="car_fum_info")
    if button_id == "car_fum_info":
        # Instead of send_text_message, use the echo_message_text template
        info_text = (
            "Our on-site Car Fumigation service uses a fogger machine, is non-oily, "
            "odor-free, and includes interior sanitization. Please tap 'Request a Quotation' if you'd like a quote."
        )
        send_template_message(
            to=from_number,
            template_name=ECHO_TEMPLATE,
            template_params=[info_text]
        )
        return

    # 5) “Return to Main Menu” (button_id="return_main_menu")
    if button_id == "return_main_menu":
        car_fumigation.send_main_menu(
            to=from_number,
            phone_number_id=phone_number_id
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    # 6) User selects a Pest Type (list_id in ["cockroach", "ants", "lizards", "other_pest"])
    if list_id in ["cockroach", "ants", "lizards", "other_pest"]:
        pest_selected = list_id
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["step"] = "awaiting_vehicle_type"
        state["pest_type"] = pest_selected
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_vehicle_type_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        return

    # 7) User selects a Vehicle Type (list_id in ["sedan", "suv", "mpv", "ultra_luxury"])
    if list_id in ["sedan", "suv", "mpv", "ultra_luxury"]:
        vehicle_selected = list_id
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["vehicle_type"] = vehicle_selected

        if vehicle_selected == "ultra_luxury":
            # Ask for free-text brand via template
            state["step"] = "awaiting_luxury_brand"
            set_user_state(CARFUM_PREFIX, from_number, state)
            prompt_text = "Please type your luxury vehicle brand (e.g., Mercedes S-Class):"
            send_template_message(
                to=from_number,
                template_name=ECHO_TEMPLATE,
                template_params=[prompt_text]
            )
            return
        else:
            # Proceed to location selection
            state["step"] = "awaiting_location"
            set_user_state(CARFUM_PREFIX, from_number, state)
            car_fumigation.send_location_list(
                to=from_number,
                phone_number_id=phone_number_id
            )
            return

    # 8) If awaiting a luxury brand (free-text)
    state = get_user_state(CARFUM_PREFIX, from_number)
    if state.get("step") == "awaiting_luxury_brand" and text_body:
        state["luxury_brand"] = text_body
        state["step"] = "awaiting_location"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_location_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        return

    # 9) User selects a Location (list_id in ["north_zone", "south_zone", "east_zone", "west_zone"])
    if list_id in ["north_zone", "south_zone", "east_zone", "west_zone"]:
        location_selected = list_id
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["location"] = location_selected

        # Compute quote
        quote_amount = car_fumigation.calculate_quote(state)
        state["quote"] = quote_amount
        state["step"] = "sent_quote_summary"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_car_fum_quote_summary(
            to=from_number,
            phone_number_id=phone_number_id,
            estimated_total=f"${quote_amount:.2f}",
            pest_reported=state["pest_type"],
            preferred_dt="(Select Date/Time next)",
            parking_address="(Select Address next)",
            vehicle_desc=(
                state["luxury_brand"]
                if state.get("vehicle_type") == "ultra_luxury"
                else state.get("vehicle_type", "")
            )
        )
        return

    # 10) User picks “ASAP” or “Enter Date/Time” (button_id)
    if button_id == "car_fum_asap":
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["appointment_method"] = "ASAP"
        state["step"] = "awaiting_parking_address"
        set_user_state(CARFUM_PREFIX, from_number, state)

        prompt_text = "Got it. Please provide your parking address now."
        send_template_message(
            to=from_number,
            template_name=ECHO_TEMPLATE,
            template_params=[prompt_text]
        )
        return

    if button_id == "car_fum_schedule":
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["appointment_method"] = "Scheduled"
        state["step"] = "awaiting_date_time"
        set_user_state(CARFUM_PREFIX, from_number, state)

        prompt_text = "Okay, please type your preferred date/time (e.g., 2025-06-10 14:00)."
        send_template_message(
            to=from_number,
            template_name=ECHO_TEMPLATE,
            template_params=[prompt_text]
        )
        return

    # 11) User typing date/time
    state = get_user_state(CARFUM_PREFIX, from_number)
    if state.get("step") == "awaiting_date_time" and text_body:
        state["preferred_date_time"] = text_body
        state["step"] = "awaiting_parking_address"
        set_user_state(CARFUM_PREFIX, from_number, state)

        prompt_text = "Thanks. Now please provide your parking address."
        send_template_message(
            to=from_number,
            template_name=ECHO_TEMPLATE,
            template_params=[prompt_text]
        )
        return

    # 12) User typing parking address
    if state.get("step") == "awaiting_parking_address" and text_body:
        state["parking_address"] = text_body
        state["step"] = "awaiting_vehicle_number"
        set_user_state(CARFUM_PREFIX, from_number, state)

        prompt_text = "Got the parking address. Please type your vehicle number (e.g., SGA1234A)."
        send_template_message(
            to=from_number,
            template_name=ECHO_TEMPLATE,
            template_params=[prompt_text]
        )
        return

    # 13) User typing vehicle number
    if state.get("step") == "awaiting_vehicle_number" and text_body:
        state["vehicle_number"] = text_body
        state["step"] = "awaiting_confirmation"
        set_user_state(CARFUM_PREFIX, from_number, state)

        # Send the final confirmation template
        car_fumigation.send_car_fum_appointment_confirmation(
            to=from_number,
            phone_number_id=phone_number_id,
            estimated_total=f"${state['quote']:.2f}",
            pest_reported=state["pest_type"],
            preferred_dt=state.get("preferred_date_time", "ASAP"),
            parking_address=state["parking_address"],
            vehicle_number=state["vehicle_number"]
        )
        return

    # 14) User answers “Yes” or “No” (button_id)
    if button_id == "car_fum_confirm_yes":
        confirmation_text = (
            "Great! Your appointment is confirmed. A human agent will reach out shortly to finalize details."
        )
        send_template_message(
            to=from_number,
            template_name=ECHO_TEMPLATE,
            template_params=[confirmation_text]
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    if button_id == "car_fum_confirm_no":
        fallback_text = (
            "No problem. You can type 'restart' to begin again or tap 'Car Fumigation' from the main menu."
        )
        send_template_message(
            to=from_number,
            template_name=ECHO_TEMPLATE,
            template_params=[fallback_text]
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    # 15) Catch‐all for anything unrecognized
    catchall_text = (
        "Sorry, I didn’t understand that. Please tap 'Need help on Pest!' or type 'menu' to see options again."
    )
    send_template_message(
        to=from_number,
        template_name=ECHO_TEMPLATE,
        template_params=[catchall_text]
    )
