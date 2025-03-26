# dispatcher.py

import flows.car_fumigation as car_fumigation
import flows.mold as mold
import flows.bedbug as bedbug

# If you have admin phone numbers:
ADMIN_NUMBERS = {"+6587788080"}
# If you have a dynamic target mapping for admin:
ADMIN_TARGET = {}

def handle_text_message(
    sender_number,
    text_body,
    sender_name,
    # data dict references
    car_fumigation_data,
    mold_removal_data,
    bedbug_data,
    live_sessions,
    # helper functions
    send_text_message,
    send_main_menu,
    initiate_live_agent,
    reset_conversation,
    # environment references
    phone_number_id,
    access_token
):
    """
    Handles all 'text' type messages. 
    """

    # --- Admin text commands ---
    if sender_number in ADMIN_NUMBERS:
        lower_text = text_body.lower()
        # Example: "appointment confirmed"
        if lower_text == "appointment confirmed":
            target = ADMIN_TARGET.get(sender_number, sender_number)
            car_fumigation.send_car_fumigation_preparation(target, phone_number_id, access_token)
            send_text_message(sender_number, f"Appointment confirmed command sent to {target}")
            return

        # Example: "commands"
        if lower_text == "commands":
            send_admin_command_menu(sender_number, send_text_message)
            return

    # --- Standard user commands ---
    if text_body.lower() == "reset":
        reset_conversation(sender_number, sender_name)
        return

    if text_body.lower() in ["live", "live agent", "agent", "connect me"]:
        initiate_live_agent(sender_number, sender_name)
        return

    # Bedbug flow: awaiting custom area text
    if sender_number in bedbug_data and bedbug_data[sender_number].get("awaiting_other_area"):
        bedbug.process_bedbug_text_message(
            sender_number,
            text_body,
            bedbug_data,
            phone_number_id,
            access_token,
            send_text_message
        )
        return

    # Car fumigation flow: awaiting vehicle model details
    if sender_number in car_fumigation_data and car_fumigation_data[sender_number].get("awaiting_vehicle_model_details"):
        car_fumigation_data[sender_number]["vehicle_details"] = text_body
        car_fumigation_data[sender_number].pop("awaiting_vehicle_model_details", None)
        send_text_message(sender_number, "Vehicle model details noted. Thank you!")
        car_fumigation.send_location_selection(sender_number, phone_number_id, access_token)
        return

    # If user is in a live session, do nothing else
    if sender_number in live_sessions and live_sessions[sender_number]:
        print("Live agent session active; no auto-bot response.")
    else:
        # Show main menu if nothing else matched
        send_main_menu(sender_number, sender_name)


def handle_interactive_message(
    sender_number,
    interactive_data,
    sender_name,
    # data dict references
    car_fumigation_data,
    mold_removal_data,
    bedbug_data,
    live_sessions,
    # helper functions
    send_text_message,
    send_interactive_message,
    send_main_menu,
    initiate_live_agent,
    reset_conversation,
    # environment references
    phone_number_id,
    access_token
):
    """
    Handles 'interactive' messages (buttons, list replies).
    """

    button_id = None
    list_id = None

    if "button_reply" in interactive_data:
        button_id = interactive_data["button_reply"]["id"]
    elif "list_reply" in interactive_data:
        list_id = interactive_data["list_reply"]["id"]

    # --- Admin Button Replies ---
    if sender_number in ADMIN_NUMBERS and button_id and button_id.startswith("admin_"):
        target = ADMIN_TARGET.get(sender_number, sender_number)
        if button_id == "admin_cfum_confirm":
            car_fumigation.send_car_fumigation_preparation(target, phone_number_id, access_token)
        elif button_id == "admin_mold_confirm":
            mold.send_mold_preparation(target, phone_number_id, access_token)
        elif button_id == "admin_bedbug_confirm":
            bedbug.process_bedbug_faq_response(target, "bbfaq_preparation", phone_number_id, access_token, send_text_message)
        elif button_id == "admin_payment_methods":
            send_text_message(
                target,
                "We accept the following payment methods:\n"
                "* PayNow...\n"
                "* Atome...\n"
                "* Cash..."
            )
        elif button_id == "admin_reset":
            reset_conversation(target, "Client")
        send_text_message(sender_number, "Admin command executed.")
        return

    # --- Admin List Replies ---
    if sender_number in ADMIN_NUMBERS and list_id and list_id.startswith("admin_"):
        target = ADMIN_TARGET.get(sender_number, sender_number)
        if list_id == "admin_cfum_confirm":
            car_fumigation.send_car_fumigation_preparation(target, phone_number_id, access_token)
        elif list_id == "admin_mold_confirm":
            mold.send_mold_preparation(target, phone_number_id, access_token)
        elif list_id == "admin_bedbug_confirm":
            bedbug.process_bedbug_faq_response(target, "bbfaq_preparation", phone_number_id, access_token, send_text_message)
        elif list_id == "admin_payment_methods":
            send_text_message(
                target,
                "We accept the following payment methods:\n"
                "* PayNow...\n"
                "* Atome...\n"
                "* Cash..."
            )
        elif list_id == "admin_reset":
            reset_conversation(target, "Client")
        send_text_message(sender_number, "Admin command executed.")
        return

    # -------------------------------
    # Normal User Interactive Flows
    # -------------------------------

    # Main Menu Buttons
    if button_id == "pest_control":
        car_fumigation.send_pest_control_dropdown(sender_number, phone_number_id, access_token)
        return
    elif button_id == "mold_removal":
        mold.send_mold_option_prompt(sender_number, phone_number_id, access_token)
        return
    elif button_id == "real_human":
        initiate_live_agent(sender_number, sender_name)
        return
    elif button_id == "return_main_menu":
        send_main_menu(sender_number, sender_name)
        return

    # Car Fumigation Flow
    if button_id == "car_fum_quote":
        car_fumigation.send_car_fumigation_followup(sender_number, phone_number_id, access_token)
        return
    if button_id in ["luxury_yes", "luxury_no"]:
        car_fumigation_data.setdefault(sender_number, {})["continental"] = button_id
        car_fumigation.send_location_selection(sender_number, phone_number_id, access_token)
        return
    if button_id == "book_appointment":
        car_fumigation.send_appointment_method_prompt(sender_number, phone_number_id, access_token)
        return
    if button_id == "apt_asap":
        car_fumigation_data.setdefault(sender_number, {})["appointment_datetime"] = "ASAP"
        send_text_message(sender_number, "Please provide your full parking address (where the vehicle will be).")
        car_fumigation_data[sender_number]["awaiting_parking_address"] = True
        return
    if button_id == "apt_enter_datetime":
        send_text_message(sender_number, "Please enter your preferred date and time for the appointment.")
        car_fumigation_data.setdefault(sender_number, {})["awaiting_appointment_datetime"] = True
        return
    if button_id == "confirm_apt_yes":
        initiate_live_agent(sender_number, sender_name)
        return
    if button_id == "confirm_apt_no":
        send_text_message(sender_number, "Let's update your appointment details. You can type your preferred date and time again.")
        car_fumigation_data[sender_number]["awaiting_appointment_datetime"] = True
        return
    if button_id == "fumigation_faq":
        car_fumigation.send_car_fumigation_faq(sender_number, phone_number_id, access_token, send_interactive_message)
        return

    # Bedbug Flow
    if button_id == "bedbug_quote":
        bedbug_data[sender_number] = {}
        bedbug.send_bedbug_area_selection(sender_number, phone_number_id, access_token, bedbug_data)
        return
    if button_id == "bedbug_more_info":
        bedbug.send_bedbug_faq_list(sender_number, phone_number_id, access_token, send_interactive_message)
        return
    if button_id == "bedbug_add_area_yes":
        bedbug.process_bedbug_area_add_confirmation(sender_number, "bedbug_add_area_yes", bedbug_data, phone_number_id, access_token, send_text_message)
        return
    if button_id == "bedbug_add_area_no":
        bedbug.process_bedbug_area_add_confirmation(sender_number, "bedbug_add_area_no", bedbug_data, phone_number_id, access_token, send_text_message)
        return
    if button_id == "bedbug_confirm_yes":
        bedbug.process_bedbug_confirmation(
            sender_number,
            "bedbug_confirm_yes",
            bedbug_data,
            phone_number_id,
            access_token,
            send_text_message,
            initiate_live_agent,
            sender_name,
            send_interactive_message=send_interactive_message
        )
        return
    if button_id == "bedbug_confirm_no":
        bedbug.process_bedbug_confirmation(
            sender_number,
            "bedbug_confirm_no",
            bedbug_data,
            phone_number_id,
            access_token,
            send_text_message,
            None,
            None
        )
        return

    # --- Mold Flow ---
    if button_id == "mold_get_quote":
        mold.new_mold_quote_flow_start(sender_number, mold_removal_data, phone_number_id, access_token)
        return
    if button_id == "mold_more_info":
        mold.send_mold_removal_faq(sender_number, phone_number_id, access_token, send_interactive_message)
        return

    # IMPORTANT: updated logic for mold confirm yes/no
    if button_id == "mold_confirm_yes":
        mold.process_mold_confirmation(
            sender_number,
            "mold_confirm_yes",
            mold_removal_data,
            phone_number_id,
            access_token,
            send_text_message,
            initiate_live_agent,
            sender_name
        )
        return
    if button_id == "mold_confirm_no":
        mold.process_mold_confirmation(
            sender_number,
            "mold_confirm_no",
            mold_removal_data,
            phone_number_id,
            access_token,
            send_text_message,
            initiate_live_agent,
            sender_name
        )
        return

    if button_id == "add_area_yes":
        mold.process_add_area_confirmation(sender_number, "yes", mold_removal_data, phone_number_id, access_token, send_text_message)
        return
    if button_id == "add_area_no":
        mold.process_add_area_confirmation(sender_number, "no", mold_removal_data, phone_number_id, access_token, send_text_message)
        return
    if button_id == "onsite_inspect_yes":
        mold_removal_data[sender_number]["onsite_inspection"] = True
        send_text_message(sender_number, "Thank you! We will arrange an onsite inspection. A live agent will follow up shortly.")
        initiate_live_agent(sender_number, sender_name)
        return
    if button_id == "onsite_inspect_no":
        mold_removal_data[sender_number]["onsite_inspection"] = False
        send_text_message(sender_number, "Understood! We can proceed with a remote assessment. A live agent will assist you shortly.")
        initiate_live_agent(sender_number, sender_name)
        return

    # List replies
    if list_id == "car_fumigation":
        car_fumigation.send_car_fumigation_options(sender_number, phone_number_id, access_token)
        return
    if list_id in [
        "car_fumigation_cockroach",
        "car_fumigation_ants",
        "car_fumigation_lizards",
        "car_fumigation_multiple",
        "car_fumigation_others"
    ]:
        car_fumigation.process_car_fumigation_pest(sender_number, list_id, car_fumigation_data, phone_number_id, access_token)
        return
    if list_id.startswith("vehicle_"):
        car_fumigation.process_vehicle_model_selection(sender_number, list_id, car_fumigation_data, phone_number_id, access_token)
        return
    if list_id.startswith("location_"):
        car_fumigation_data.setdefault(sender_number, {})["location"] = list_id
        car_fumigation.compute_and_send_quote(sender_number, car_fumigation_data, phone_number_id, access_token, send_text_message)
        return
    if list_id.startswith("cfq_"):
        car_fumigation.process_car_fumigation_faq_response(sender_number, list_id, phone_number_id, access_token)
        return

    if list_id == "bed_bugs":
        bedbug.send_bedbug_initial_menu(sender_number, phone_number_id, access_token)
        return
    if list_id.startswith("bedbug_area_"):
        bedbug.process_bedbug_area_selection(sender_number, list_id, bedbug_data, phone_number_id, access_token, send_text_message)
        return
    if list_id.startswith("bedbug_bed_count_"):
        bedbug.process_bedbug_bedroom_count_selection(sender_number, list_id, bedbug_data, phone_number_id, access_token, send_text_message)
        return
    if list_id.startswith("bedbug_count_"):
        bedbug.process_bedbug_count_selection(sender_number, list_id, bedbug_data, phone_number_id, access_token, send_text_message)
        return
    if list_id.startswith("bbfaq_"):
        bedbug.process_bedbug_faq_response(sender_number, list_id, phone_number_id, access_token, send_text_message)
        return

    # Mold list replies
    if list_id.startswith("area_"):
        mold.process_mold_area_selection(sender_number, list_id, mold_removal_data, phone_number_id, access_token, send_text_message)
        return
    if list_id in ["growth_ceiling", "growth_walls", "growth_both"]:
        mold.process_growth_location_choice(sender_number, list_id, mold_removal_data, phone_number_id, access_token, send_text_message)
        return
    if list_id.startswith("mfaq_"):
        mold.process_mold_faq_response(sender_number, list_id, mold_removal_data, phone_number_id, access_token)
        return
    if list_id.startswith("bedroom_count_"):
        if list_id == "bedroom_count_1":
            mold_removal_data[sender_number]["bedroom_count"] = "1 bedroom"
        elif list_id == "bedroom_count_2":
            mold_removal_data[sender_number]["bedroom_count"] = "2 bedrooms"
        else:
            mold_removal_data[sender_number]["bedroom_count"] = "3+ bedrooms"
        mold_removal_data[sender_number].pop("awaiting_bedroom_count", None)
        mold.send_add_area_confirmation_prompt(sender_number, phone_number_id, access_token, mold_removal_data)
        return
    if list_id.startswith("bathroom_count_"):
        if list_id == "bathroom_count_1":
            mold_removal_data[sender_number]["bathroom_count"] = "1 bathroom"
        elif list_id == "bathroom_count_2":
            mold_removal_data[sender_number]["bathroom_count"] = "2 bathrooms"
        else:
            mold_removal_data[sender_number]["bathroom_count"] = "3+ bathrooms"
        mold_removal_data[sender_number].pop("awaiting_bathroom_count", None)
        mold.send_add_area_confirmation_prompt(sender_number, phone_number_id, access_token, mold_removal_data)
        return

    # Fallback
    send_text_message(sender_number, "Unrecognized interactive selection.")


##############################
# Optional: Admin Menu Helper
##############################
def send_admin_command_menu(admin_number, send_text_message):
    """
    If you want a function to show the admin command menu. 
    Here, we pass 'send_text_message' or 'send_interactive_message' to do so.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": admin_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Admin Commands"},
            "body": {"text": "Select a command:"},
            "footer": {"text": "Admin Options"},
            "action": {
                "button": "Select Command",
                "sections": [{
                    "title": "Master Cmds",
                    "rows": [
                        {
                            "id": "admin_cfum_confirm",
                            "title": "Car Fum Confirm",
                            "description": "Send car fum prep text"
                        },
                        {
                            "id": "admin_mold_confirm",
                            "title": "Mold Rem Confirm",
                            "description": "Send mold prep text"
                        },
                        {
                            "id": "admin_bedbug_confirm",
                            "title": "Bed Bug Confirm",
                            "description": "Send bed bug prep text"
                        },
                        {
                            "id": "admin_payment_methods",
                            "title": "Payment Methods",
                            "description": "Send payment FAQ"
                        },
                        {
                            "id": "admin_reset",
                            "title": "Reset Conversation",
                            "description": "Reset client convo"
                        }
                    ]
                }]
            }
        }
    }
    # if you want to show it as interactive, do something like:
    # send_interactive_message(admin_number, payload)
    # or if you want just text, do something else
    # We'll just do a text message for simplicity:
    send_text_message(admin_number, "Admin command menu not implemented fully here.")
