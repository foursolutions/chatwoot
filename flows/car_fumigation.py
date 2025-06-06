# flows/car_fumigation.py

import os
from flask import Response
from helpers import (
    send_text_message,
    send_list_message,
    send_template_message,
    get_user_state,
    set_user_state,
    clear_user_state
)

PREFIX = "car"

def handle_car_fumigation_flow(to_chat_id: str, message: dict, api_key: str, base_url: str):
    """
    Drives the Car Fumigation flow. Expects to find Redis state under key "car:<phone>".
    """

    # 1) Fetch current step from Redis (or start fresh)
    state = get_user_state(PREFIX, to_chat_id) or {}
    step = state.get("step", "")

    # ──────────────────────────────────────────────────────────────────────────────
    # STEP 1: User tapped "Need help on Pest!"
    # ──────────────────────────────────────────────────────────────────────────────
    if step == "start":
        # Move to next step and re‐store in Redis
        state["step"] = "select_pest_type"
        set_user_state(PREFIX, to_chat_id, state)

        body = "Please select the pest service you need:\n"
        header = "Pest Control Services"
        footer = "Tap to choose"
        action = "Select Service"
        sections = [
            {
                "title": "Common Pest Issues",
                "rows": [
                    {
                        "id": "car_fumigation",
                        "title": "Car Fumigation 🚗",
                        "description": "On-site fumigation & fogging"
                    },
                    {
                        "id": "home_pest",
                        "title": "Home Pest Control 🏠",
                        "description": "Cockroaches, ants, termites, etc."
                    },
                    {
                        "id": "commercial_pest",
                        "title": "Commercial Pest 🚛",
                        "description": "Factories, offices, warehouses"
                    }
                ]
            }
        ]
        resp = send_list_message(
            to=to_chat_id,
            body=body,
            header=header,
            footer=footer,
            action_title=action,
            sections=sections
        )
        print(f"[DEBUG] send_pest_type_list → {resp}")
        return Response(status=200)

    # ──────────────────────────────────────────────────────────────────────────────
    # STEP 2: After user picks a pest type (interactive LIST reply)
    # ──────────────────────────────────────────────────────────────────────────────
    if message.get("type") == "interactive" and message["interactive"].get("type") == "list_reply":
        # Grab list‐reply ID
        pest_choice = message["interactive"]["list_reply"]["id"]
        state["pest_type"] = pest_choice

        # Move to "select_vehicle_type"
        state["step"] = "select_vehicle_type"
        set_user_state(PREFIX, to_chat_id, state)

        body = "What type of vehicle do you drive?"
        header = "Select Vehicle Type"
        footer = "Tap to choose"
        action = "Select Vehicle Type"
        sections = [
            {
                "title": "Vehicle Types",
                "rows": [
                    { "id": "vehicle_sedan",  "title": "Sedan/Hatchback",    "description": "Standard cars" },
                    { "id": "vehicle_suv",    "title": "SUV",                "description": "Sport Utility Vehicle" },
                    { "id": "vehicle_mpv",    "title": "MPV",                "description": "Multi-Purpose Vehicle" },
                    { "id": "vehicle_vans",   "title": "Vans/Lorries",       "description": "Commercial vehicles" },
                    { "id": "vehicle_ultra",  "title": "Super/Luxury Cars",  "description": "e.g. Bentley, Ferrari, etc." },
                    { "id": "vehicle_others", "title": "Other",              "description": "Other vehicle types" }
                ]
            }
        ]
        resp = send_list_message(
            to=to_chat_id,
            body=body,
            header=header,
            footer=footer,
            action_title=action,
            sections=sections
        )
        print(f"[DEBUG] send_vehicle_type_list → {resp}")
        return Response(status=200)

    # ──────────────────────────────────────────────────────────────────────────────
    # STEP 3: After user picks a vehicle type
    # ──────────────────────────────────────────────────────────────────────────────
    if message.get("type") == "interactive" and state.get("step") == "select_vehicle_type":
        vehicle_choice = message["interactive"]["list_reply"]["id"]
        state["vehicle"] = vehicle_choice

        # If user chose "ultra" or "others", skip to a manual quote summary:
        if vehicle_choice in ["vehicle_ultra", "vehicle_others"]:
            state["step"] = "quote_summary"
            set_user_state(PREFIX, to_chat_id, state)

            text = (
                "On-Site Car Fumigation Quotation\n"
                f"Service chosen: {state['pest_type']}\n"
                f"Vehicle: {vehicle_choice}\n\n"
                "Please wait for our technician to contact you shortly."
            )
            send_text_message({
                "to": to_chat_id,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": text }
            })
            return Response(status=200)

        # Otherwise, ask about additional care fee (Yes/No):
        state["step"] = "ask_luxury_brand"
        set_user_state(PREFIX, to_chat_id, state)

        prompt = (
            "Does your vehicle belong to any of these brands?\n\n"
            "• Mercedes-Benz\n"
            "• BMW\n"
            "• Audi\n"
            "• Lexus\n"
            "• Porsche\n"
            "• Jaguar\n"
            "• Tesla\n"
            "• Range Rover\n\n"
            "These brands require special care during servicing.\n"
            "Please reply Yes or No."
        )
        send_text_message({
            "to": to_chat_id,
            "type": "text",
            "messaging_product": "whatsapp",
            "text": { "body": prompt }
        })
        return Response(status=200)

    # ──────────────────────────────────────────────────────────────────────────────
    # STEP 4: User replies “Yes” / “No” to additional care fee question
    # ──────────────────────────────────────────────────────────────────────────────
    if message.get("type") == "chat" and state.get("step") == "ask_luxury_brand":
        text = message.get("body", "").strip().lower()
        if text in ["yes", "no"]:
            state["luxury_brand"] = (text == "yes")
            state["step"] = "final_quote_summary"
            set_user_state(PREFIX, to_chat_id, state)

            summary = (
                f"Your pest service: {state['pest_type']}\n"
                f"Vehicle type: {state['vehicle']}\n"
                f"Luxury brand care: {'Yes' if state['luxury_brand'] else 'No'}\n\n"
                "Estimated quote: SG$"
                f"{'120' if state['luxury_brand'] else '80'}\n\n"
                "Reply “Confirm” to book, or “Cancel” to return to main menu."
            )
            send_text_message({
                "to": to_chat_id,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": summary }
            })
            return Response(status=200)

        # If invalid reply:
        send_text_message({
            "to": to_chat_id,
            "type": "text",
            "messaging_product": "whatsapp",
            "text": { "body": "Please reply exactly Yes or No." }
        })
        return Response(status=200)

    # ──────────────────────────────────────────────────────────────────────────────
    # STEP 5: Finalate: user types “Confirm” or “Cancel”
    # ──────────────────────────────────────────────────────────────────────────────
    if message.get("type") == "chat" and state.get("step") == "final_quote_summary":
        text = message.get("body", "").strip().lower()

        if text == "confirm":
            send_text_message({
                "to": to_chat_id,
                "type": "text",
                "messaging_product": "whatsapp",
                "text": { "body": "✅ Thank you! Your booking is confirmed. Our technician will be in touch soon." }
            })
            clear_user_state(PREFIX, to_chat_id)
            return Response(status=200)

        if text == "cancel":
            clear_user_state(PREFIX, to_chat_id)
            # Send main menu template again
            send_template_message(
                to=to_chat_id,
                template_name=MAIN_MENU_TEMPLATE,
                template_params=["there"]
            )
            return Response(status=200)

        # If unrecognized:
        send_text_message({
            "to": to_chat_id,
            "type": "text",
            "messaging_product": "whatsapp",
            "text": { "body": "Please type Confirm or Cancel." }
        })
        return Response(status=200)

    # ──────────────────────────────────────────────────────────────────────────────
    # If no step matched, simply 200
    # ──────────────────────────────────────────────────────────────────────────────
    return Response(status=200)
