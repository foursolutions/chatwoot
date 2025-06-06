# flows/car_fumigation.py
from helpers import (
    get_user_state,
    set_user_state,
    clear_user_state,
    send_text_message,
    send_template_message,
    send_list_message
)

PREFIX = "CAR_FUM"

def handle_car_fumigation_flow(chat_id: str, msg: dict) -> None:
    """
    Main handler for Car Fumigation flow.
    Steps:
      0 → Send vehicle‐type list
      1 → Expect list_reply: save vehicle_type, ask for license plate
      2 → Expect text: save license_plate, send date list
      3 → Expect list_reply: save appointment_date, send time list
      4 → Expect list_reply: save appointment_time, send confirmation template
      5 → Expect button_reply: either finalize or cancel
    """
    # 1. Load any saved state
    state = get_user_state(PREFIX, chat_id) or {}
    step = state.get("step", 0)

    # ─── Step 0: First time in CAR_FUM ──────────────────────────────────────────────
    if step == 0:
        sections = [
            {
                "title": "Choose Vehicle Type",
                "rows": [
                    {"id": "car_fum_sedan",    "title": "Sedan",     "description": "Standard 4‐door sedan"},
                    {"id": "car_fum_hatchback","title": "Hatchback", "description": "Compact hatchback"},
                    {"id": "car_fum_suv",      "title": "SUV",       "description": "Sports Utility Vehicle"},
                    {"id": "car_fum_truck",    "title": "Truck",     "description": "Light Truck / Van"}
                ]
            }
        ]
        action_label = "Select Vehicle"
        print(f"ℹ️ Sending vehicle‐type list to {chat_id} (step 0).")
        send_list_message(
            to=chat_id,
            body="Please select your vehicle type:",
            header="Car Fumigation Options",
            footer="Four Solutions Pte Ltd",
            action=action_label,
            sections=sections
        )
        state["step"] = 1
        set_user_state(PREFIX, chat_id, state)
        return

    # ─── Step 1: Expecting list_reply with vehicle_type ───────────────────────────
    if step == 1:
        if msg.get("type") == "list_reply":
            selected_id = msg["list_reply"]["id"]  # e.g. "car_fum_sedan"
            print(f"ℹ️ Received vehicle_type = {selected_id} from {chat_id}")
            state["vehicle_type"] = selected_id
            state["step"] = 2
            set_user_state(PREFIX, chat_id, state)

            # Ask for license plate (free‐text)
            send_text_message(
                to=chat_id,
                body="Great! What’s your car’s license plate number?",
                footer="(e.g. SSM1234A)"
            )
            return
        else:
            # They didn’t click a list row—prompt again
            send_text_message(
                to=chat_id,
                body="⚠️ Please select your vehicle type from the list above."
            )
            return

    # ─── Step 2: Expecting license plate text ───────────────────────────────────────
    if step == 2:
        if msg.get("type") in ("text", "conversation"):
            plate = msg.get("text", {}).get("body", "").strip().upper()
            print(f"ℹ️ Received license_plate = {plate} from {chat_id}")
            state["license_plate"] = plate
            state["step"] = 3
            set_user_state(PREFIX, chat_id, state)

            # Next: ask for appointment date via list
            sections = [
                {
                    "title": "Select Date",
                    "rows": [
                        {"id":"date_2025-06-10", "title":"10 June 2025", "description":""},
                        {"id":"date_2025-06-11", "title":"11 June 2025", "description":""},
                        {"id":"date_2025-06-12", "title":"12 June 2025", "description":""}
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
            send_text_message(
                to=chat_id,
                body="⚠️ Please type your license plate (e.g. SSM1234A)."
            )
            return

    # ─── Step 3: Expecting list_reply with appointment_date ────────────────────────
    if step == 3:
        if msg.get("type") == "list_reply":
            selected_date = msg["list_reply"]["id"]  # e.g. "date_2025-06-10"
            print(f"ℹ️ Received appointment_date = {selected_date} from {chat_id}")
            state["appointment_date"] = selected_date
            state["step"] = 4
            set_user_state(PREFIX, chat_id, state)

            # Next: ask for time slot
            sections = [
                {
                    "title": "Select Time",
                    "rows": [
                        {"id":"time_0900", "title":"09:00 AM", "description":""},
                        {"id":"time_1300", "title":"01:00 PM", "description":""},
                        {"id":"time_1700", "title":"05:00 PM", "description":""}
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
                body="⚠️ Please choose a valid date from the list."
            )
            return

    # ─── Step 4: Expecting list_reply with appointment_time ───────────────────────
    if step == 4:
        if msg.get("type") == "list_reply":
            selected_time = msg["list_reply"]["id"]  # e.g. "time_0900"
            print(f"ℹ️ Received appointment_time = {selected_time} from {chat_id}")
            state["appointment_time"] = selected_time
            state["step"] = 5
            set_user_state(PREFIX, chat_id, state)

            # Next: send a confirmation template with buttons (yes/no)
            # Suppose you have a template named "car_fum_appointment_confirmation"
            # with placeholders for plate, date, and time.
            template_params = [
                state["license_plate"],     # e.g. "SSM1234A"
                state["appointment_date"],  # e.g. "date_2025-06-10"
                state["appointment_time"]   # e.g. "time_0900"
            ]
            print("ℹ️ Sending appointment confirmation template to", chat_id)
            send_template_message(
                to=chat_id,
                template_name="car_fum_appointment_confirmation",
                template_params=template_params
            )
            return
        else:
            send_text_message(
                to=chat_id,
                body="⚠️ Please select a valid time from the list."
            )
            return

    # ─── Step 5: Expecting button_reply to confirm or cancel ───────────────────────
    if step == 5:
        if msg.get("type") == "button_reply":
            btn_id = msg["button_reply"]["id"]
            print(f"ℹ️ Received confirmation button id = {btn_id} from {chat_id}")
            if btn_id == "car_fum_confirm_yes":
                # Finalize the quote, send summary template
                print("ℹ️ User confirmed. Sending quote summary.")
                send_template_message(
                    to=chat_id,
                    template_name="car_fum_quote_summary",
                    template_params=[
                        state["license_plate"],
                        state["appointment_date"],
                        state["appointment_time"]
                    ]
                )
                clear_user_state(PREFIX, chat_id)
                return
            elif btn_id == "car_fum_confirm_no":
                # User canceled—go back to MAIN_MENU
                print("ℹ️ User canceled appointment. Returning to main menu.")
                clear_user_state(PREFIX, chat_id)
                send_template_message(
                    to=chat_id,
                    template_name="main_menu_v2",
                    template_params=[]
                )
                return
        else:
            send_text_message(
                to=chat_id,
                body="⚠️ Please tap one of the buttons (Yes or No)."
            )
            return

    # ─── Fallback: Unrecognized input ───────────────────────────────────────────────
    send_text_message(
        to=chat_id,
        body="⚠️ Sorry, I didn’t understand that. Please type “reset” to return to the main menu."
    )
