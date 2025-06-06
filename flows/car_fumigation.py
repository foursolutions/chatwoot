# flows/car_fumigation.py
from helpers import get_user_state, set_user_state, clear_user_state, send_text_message, send_template_message, send_list_message

# Prefix used in Redis so that car fumigation state does not collide with other flows
PREFIX = "CAR_FUM"

def handle_car_fumigation_flow(chat_id: str, msg: dict) -> None:
    """
    The main entry point for Car Fumigation flow. 
    - If there is no existing state, send the first list or template to ask "Which vehicle?"
    - Otherwise, read msg content and branch accordingly.
    """
    # 1. Load any saved state
    state = get_user_state(PREFIX, chat_id)  # e.g. {"step": 1, "vehicle": "Honda"}
    step = state.get("step", 0)

    # 2. If step == 0, this is the first time we see them in CAR_FUM
    if step == 0:
        # e.g. send a list of options: "Select your vehicle type"
        sections = [
            {
                "title": "Choose Vehicle Type",
                "rows": [
                    {"id": "car_fum_sedan",    "title": "Sedan",    "description": "Standard 4‐door sedan"},
                    {"id": "car_fum_hatchback","title": "Hatchback","description": "Compact hatchback"},
                    {"id": "car_fum_suv",      "title": "SUV",      "description": "Sports Utility Vehicle"},
                    {"id": "car_fum_truck",    "title": "Truck",    "description": "Light Truck / Van"}
                ]
            }
        ]
        # The “action” label is the text on the button at the bottom of the list
        action_label = "Select Vehicle"
        send_list_message(
            to=chat_id,
            body="Please select your vehicle type:",
            header="Car Fumigation Options",
            footer="Four Solutions Pte Ltd",
            action=action_label,
            sections=sections
        )
        # Mark state: next time we’re expecting a vehicle selection (step 1)
        set_user_state(PREFIX, chat_id, {"step": 1})
        return

    # 3. If step == 1, we expect the user’s selection from the above list:
    if step == 1:
        # If user clicked a list row, 1msg will post back:
        # msg["type"] == "list_reply"
        # msg["list_reply"]["id"] == one of "car_fum_sedan", etc.
        if msg.get("type") == "list_reply":
            selected_id = msg["list_reply"]["id"]  # e.g. "car_fum_sedan"
            # Save their selection
            state["vehicle_type"] = selected_id
            state["step"] = 2
            set_user_state(PREFIX, chat_id, state)

            # Next: ask for location (maybe as a text prompt or another list)
            send_text_message(
                to=chat_id,
                body="Great! What’s your car’s license plate number?",
                footer="Reply with your plate (e.g. SSM1234A)."
            )
            return
        else:
            # If they typed something unexpected, repeat the list
            send_text_message(
                to=chat_id,
                body="Sorry, please select your vehicle type from the list above."
            )
            return

    # 4. If step == 2, we expect them to type a license plate (free‐text).
    if step == 2:
        if msg.get("type") == "text":
            plate = msg["text"]["body"].strip().upper()
            state["license_plate"] = plate
            state["step"] = 3
            set_user_state(PREFIX, chat_id, state)

            # Next: ask for appointment date/time via another list
            sections = [
                {
                    "title": "Select Date",
                    "rows": [
                        {"id": "date_2025-06-10", "title": "10 June 2025", "description": ""},
                        {"id": "date_2025-06-11", "title": "11 June 2025", "description": ""},
                        {"id": "date_2025-06-12", "title": "12 June 2025", "description": ""},
                    ]
                }
            ]
            send_list_message(
                to=chat_id,
                body="When would you like to schedule your car fumigation?",
                header="Choose a Date",
                footer="Four Solutions Pte Ltd",
                action="Select Date",
                sections=sections
            )
            return
        else:
            # They must send text for the license plate
            send_text_message(
                to=chat_id,
                body="Please type your license plate (e.g. SSM1234A)."
            )
            return

    # 5. If step == 3, we expect a list reply for date:
    if step == 3:
        if msg.get("type") == "list_reply":
            selected_date = msg["list_reply"]["id"]  # e.g. "date_2025-06-10"
            state["appointment_date"] = selected_date
            state["step"] = 4
            set_user_state(PREFIX, chat_id, state)

            # Next: Send time‐slot options (another list)
            sections = [
                {
                    "title": "Select Time",
                    "rows": [
                        {"id": "time_0900",  "title": "09:00 AM",  "description": ""},
                        {"id": "time_1300",  "title": "01:00 PM",  "description": ""},
                        {"id": "time_1700",  "title": "05:00 PM",  "description": ""},
                    ]
                }
            ]
            send_list_message(
                to=chat_id,
                body="Choose a time slot:",
                header="Select Time",
                footer="Four Solutions Pte Ltd",
                action="Select Time",
                sections=sections
            )
            return
        else:
            send_text_message(
                to=chat_id,
                body="Please choose a valid date from the list."
            )
            return

    # 6. If step == 4, we expect a list reply for time:
    if step == 4:
        if msg.get("type") == "list_reply":
            selected_time = msg["list_reply"]["id"]  # e.g. "time_0900"
            state["appointment_time"] = selected_time
            state["step"] = 5
            set_user_state(PREFIX, chat_id, state)

            # Next: confirm via template or buttons
            # Suppose you have a template called "car_fum_appointment_confirmation"
            # with placeholders for date, time, plate, etc.
            template_params = [
                state["license_plate"],    # e.g. "SSM1234A"
                state["appointment_date"], # e.g. "date_2025-06-10"
                state["appointment_time"]  # e.g. "time_0900"
            ]
            send_template_message(
                to=chat_id,
                template_name="car_fum_appointment_confirmation",
                template_params=template_params
            )
            return
        else:
            send_text_message(
                to=chat_id,
                body="Please select a valid time from the list."
            )
            return

    # 7. If step == 5, we might be waiting for them to confirm or cancel:
    if step == 5:
        # If your confirmation template had quick‐reply buttons (e.g. "Yes" / "No"),
        # handle those IDs here. For example, if they clicked id="car_fum_confirm_yes":
        if msg.get("type") == "button_reply":
            btn_id = msg["button_reply"]["id"]
            if btn_id == "car_fum_confirm_yes":
                # Finalize the quote, send summary
                send_template_message(
                    to=chat_id,
                    template_name="car_fum_quote_summary",
                    template_params=[ state["license_plate"], state["appointment_date"], state["appointment_time"] ]
                )
                # Clear the user state so next time they must start fresh or type "reset"
                clear_user_state(PREFIX, chat_id)
                return
            elif btn_id == "car_fum_confirm_no":
                # User canceled—redirect back to MAIN_MENU or restart CAR_FUM flow
                clear_user_state(PREFIX, chat_id)
                send_template_message(to=chat_id, template_name="main_menu_v2", template_params=[])
                return
        else:
            # If they typed something else (text), prompt them to click a button
            send_text_message(
                to=chat_id,
                body="Please tap one of the buttons to confirm or cancel."
            )
            return

    # 8. Fallback: If none of the above, send an error or restart
    send_text_message(
        to=chat_id,
        body="Sorry, I didn’t understand. Please type “reset” to return to the main menu."
    )
