# dispatcher.py
import os
import json
import requests
from flows import car_fumigation  # only import flow functions (no shared helpers here)
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_template_message,
    send_interactive_message,
)

# ====================
# Environment / Config
# ====================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE")

# Prefix for Car Fumigation user‐state in Redis
CARFUM_PREFIX = "carfum"

# ===========================
# Main Webhook Event Handler
# ===========================
def handle_event(payload: dict):
    """
    Called from main.py whenever a message/event arrives from Meta/360dialog.
    We parse out contacts → message type → interactive or text, then route.
    """
    if payload.get("object") != "whatsapp_business_account":
        return

    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            val = change.get("value", {})
            messages = val.get("messages", [])
            metadata = val.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", PHONE_NUMBER_ID)

            for message in messages:
                from_number = message.get("from")         # e.g. "6591234567"
                msg_type = message.get("type")

                button_id = None
                list_id = None
                text_body = None

                # 1) Extract interactive/button or list replies
                if msg_type == "interactive":
                    interactive = message.get("interactive", {})
                    itype = interactive.get("type")
                    if itype == "button_reply":
                        button_id = interactive["button_reply"]["id"]
                    elif itype == "list_reply":
                        list_id = interactive["list_reply"]["id"]

                # 2) If not interactive, check if it's plain text
                elif msg_type == "text":
                    text_body = message["text"]["body"].strip().lower()

                # 3) Route based on button_id, list_id, or text
                route_user(
                    from_number,
                    button_id,
                    list_id,
                    text_body,
                    phone_number_id
                )

def route_user(from_number, button_id, list_id, text_body, phone_number_id):
    """
    Using button_id, list_id, or text_body, decide what to do.
    We focus on the Car Fumigation flow first. Later you can add bedbug_flow, mold_flow, etc.
    """

    # 1) If user tapped “Need help on Pest!” (template button_id="pest_control")
    if button_id == "pest_control":
        car_fumigation.send_pest_control_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        state = {"step": "sent_pest_list"}
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # 2) If user chose “Car Fumigation” from that list:
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

    # 3) From Car Fumigation menu, user taps “Request a Quotation” (button_id="car_fum_quote")
    if button_id == "car_fum_quote":
        car_fumigation.send_pest_type_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["step"] = "awaiting_pest_type"
        set_user_state(CARFUM_PREFIX, from_number, state)
        return

    # 4) From Car Fumigation menu, user taps “More Info on Service” (button_id="car_fum_info")
    if button_id == "car_fum_info":
        text = (
            "Our on‐site Car Fumigation service uses a fogger machine, is "
            "non‐oily, odor‐free, and includes interior sanitization.\n"
            "Please tap 'Request a Quotation' if you'd like a quote."
        )
        send_text_message(to=from_number, body=text)
        return

    # 5) From Car Fumigation menu, user taps “Return to Main Menu” (button_id="return_main_menu")
    if button_id == "return_main_menu":
        car_fumigation.send_main_menu(
            to=from_number,
            phone_number_id=phone_number_id
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    # 6) Car Fumigation: User selecting a Pest Type in a list
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

    # 7) Car Fumigation: User selecting a Vehicle Type
    if list_id in ["sedan", "suv", "mpv", "ultra_luxury"]:
        vehicle_selected = list_id
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["vehicle_type"] = vehicle_selected

        if vehicle_selected == "ultra_luxury":
            state["step"] = "awaiting_luxury_brand"
            set_user_state(CARFUM_PREFIX, from_number, state)
            send_text_message(
                to=from_number,
                body="Please type your luxury vehicle brand (e.g., Mercedes S-Class):"
            )
            return
        else:
            state["step"] = "awaiting_location"
            set_user_state(CARFUM_PREFIX, from_number, state)
            car_fumigation.send_location_list(
                to=from_number,
                phone_number_id=phone_number_id
            )
            return

    # 8) Car Fumigation: If awaiting luxury brand (free‐text)
    state = get_user_state(CARFUM_PREFIX, from_number)
    if state.get("step") == "awaiting_luxury_brand" and text_body:
        luxury_brand = text_body
        state["luxury_brand"] = luxury_brand
        state["step"] = "awaiting_location"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_location_list(
            to=from_number,
            phone_number_id=phone_number_id
        )
        return

    # 9) Car Fumigation: User choosing a Location
    if list_id in ["north_zone", "south_zone", "east_zone", "west_zone"]:
        location_selected = list_id
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["location"] = location_selected
        quote_amount = car_fumigation.calculate_quote(state)
        state["quote"] = quote_amount
        state["step"] = "sent_quote_summary"
        set_user_state(CARFUM_PREFIX, from_number, state)

        car_fumigation.send_car_fum_quote_summary(
            to=from_number,
            phone_number_id=phone_number_id,
            estimated_total=f"${quote_amount:.2f}",
            pest_reported=state["pest_type"],
            preferred_dt="(Select Date/Time next)",   # placeholder
            parking_address="(Select Address next)",
            vehicle_desc=(
                state["luxury_brand"]
                if state.get("vehicle_type") == "ultra_luxury"
                else state.get("vehicle_type", "")
            )
        )
        return

    # 10) User choosing appointment‐method (button_id="car_fum_asap" or "car_fum_schedule")
    if button_id == "car_fum_asap":
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["appointment_method"] = "ASAP"
        state["step"] = "awaiting_parking_address"
        set_user_state(CARFUM_PREFIX, from_number, state)

        send_text_message(
            to=from_number,
            body="Got it. Please provide your parking address now."
        )
        return

    if button_id == "car_fum_schedule":
        state = get_user_state(CARFUM_PREFIX, from_number)
        state["appointment_method"] = "Scheduled"
        state["step"] = "awaiting_date_time"
        set_user_state(CARFUM_PREFIX, from_number, state)

        send_text_message(
            to=from_number,
            body="Okay, please type your preferred date/time (e.g., 2025-06-10 14:00)."
        )
        return

    # 11) User typing date/time
    state = get_user_state(CARFUM_PREFIX, from_number)
    if state.get("step") == "awaiting_date_time" and text_body:
        state["preferred_date_time"] = text_body
        state["step"] = "awaiting_parking_address"
        set_user_state(CARFUM_PREFIX, from_number, state)

        send_text_message(
            to=from_number,
            body="Thanks. Now please provide your parking address."
        )
        return

    # 12) User typing parking address
    if state.get("step") == "awaiting_parking_address" and text_body:
        state["parking_address"] = text_body
        state["step"] = "awaiting_vehicle_number"
        set_user_state(CARFUM_PREFIX, from_number, state)

        send_text_message(
            to=from_number,
            body="Got the parking address. Please type your vehicle number (e.g., SGA1234A)."
        )
        return

    # 13) User typing vehicle number
    if state.get("step") == "awaiting_vehicle_number" and text_body:
        state["vehicle_number"] = text_body
        state["step"] = "awaiting_confirmation"
        set_user_state(CARFUM_PREFIX, from_number, state)

        send_car_fum_appointment_confirmation(
            to=from_number,
            phone_number_id=phone_number_id,
            estimated_total=f"${state['quote']:.2f}",
            pest_reported=state["pest_type"],
            preferred_dt=state.get("preferred_date_time", "ASAP"),
            parking_address=state["parking_address"],
            vehicle_number=state["vehicle_number"]
        )
        return

    # 14) User responds “Yes” or “No” to confirmation
    if button_id == "car_fum_confirm_yes":
        send_text_message(
            to=from_number,
            body=(
                "Great! Your appointment is confirmed. "
                "A human agent will reach out shortly to finalize details."
            )
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    if button_id == "car_fum_confirm_no":
        send_text_message(
            to=from_number,
            body="No problem. You can type 'restart' to begin again or tap 'Car Fumigation' from the main menu."
        )
        clear_user_state(CARFUM_PREFIX, from_number)
        return

    # 15) Catch‐all: if nothing matched
    send_text_message(
        to=from_number,
        body=(
            "Sorry, I didn’t understand that. Please tap 'Need help on Pest!' "
            "or type 'menu' to see options again."
        )
    )
