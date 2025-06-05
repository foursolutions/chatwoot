# helpers.py

import os
import requests

# ────────────────────────────────────────────────────────────────────────────────
# 1msg / WhatsApp configuration
# ────────────────────────────────────────────────────────────────────────────────
API_KEY_WA  = os.environ.get("WHATSAPP_TOKEN", "")   # e.g. "TKNgrBqpmnbDhf9NzyO5uXNgKHoblDCe"
INSTANCE_ID = "VAN388218473"                          # your 1msg instance ID

# ────────────────────────────────────────────────────────────────────────────────
# send_text_message: Sends a plain text message via 1msg’s /send endpoint
# ────────────────────────────────────────────────────────────────────────────────
def send_text_message(message_payload: dict) -> dict:
    """
    message_payload should include:
    {
      "to": "<plain_phone>",         # e.g. "6587788080"
      "type": "text",
      "messaging_product": "whatsapp",
      "text": { "body": "Hello!" }
    }
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/send"
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=message_payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return { "error": "non-json response", "status_code": resp.status_code }


# ────────────────────────────────────────────────────────────────────────────────
# send_template_message: Sends a pre-approved WhatsApp Template via 1msg’s /sendTemplate
# ────────────────────────────────────────────────────────────────────────────────
def send_template_message(to: str, template_name: str, template_params: list) -> dict:
    """
    to: the chatId phone number **without “@c.us”**, e.g. "6587788080"
    template_name: name of your approved template (e.g. "main_menu_v2")
    template_params: list of strings for body‐placeholders
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendTemplate"
    headers = { "Content-Type": "application/json" }

    params_array = []
    for p in template_params:
        params_array.append({
            "type": "body",
            "parameters": [
                { "type": "text", "text": p }
            ]
        })

    payload = {
        "token": API_KEY_WA,
        # If you use a namespace in WhatsApp for templates, set it here.
        # If you do not use a namespace, leave this as an empty string or omit the field entirely.
        "namespace": os.environ.get("WHATSAPP_NAMESPACE", ""),
        "template": template_name,
        "language": { "policy": "deterministic", "code": "en" },
        "params": params_array,
        "phone": to   # <— 1msg expects the phone number as plain digits (no “@c.us”)
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return { "error": "non-json response", "status_code": resp.status_code }


# ────────────────────────────────────────────────────────────────────────────────
# send_list_message: Sends a WhatsApp "interactive list" via 1msg’s /sendList endpoint
# ────────────────────────────────────────────────────────────────────────────────
def send_list_message(to_chat_id: str) -> dict:
    """
    to_chat_id must be the full WhatsApp ID, e.g. "6587788080@c.us".
    Returns whichever JSON 1msg sends back.
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendList"
    headers = { "Content-Type": "application/json" }

    payload = {
        "token": API_KEY_WA,
        # The “body” text that appears above the rows of your list:
        "body":   "Please select the pest control service you need assistance with:\n",
        # The “header” text at the top:
        "header": "Pest Control Services",
        # The “footer” text at the bottom:
        "footer": "Tap to choose",
        # The button label that opens the list:
        "action": "Select Service",
        # Exactly one “section,” called “Common Pest Issues,” with each row defined:
        "sections": [
            {
                "title": "Common Pest Issues",
                "rows": [
                    {
                        "id": "car_fumigation",
                        "title": "Car Fumigation 🚗",
                        "description": "On-site fumigation & fogging"
                    },
                    {
                        "id": "bedbugs",
                        "title": "Bed Bugs 🛏️",
                        "description": "Elimination of bed bugs"
                    },
                    {
                        "id": "booklice",
                        "title": "Booklice 📚",
                        "description": "Treatment for booklice"
                    },
                    {
                        "id": "roaches_ants",
                        "title": "Roaches & Ants 🐜",
                        "description": "General pest control"
                    },
                    {
                        "id": "bees_wasps",
                        "title": "Bees/Wasps 🐝",
                        "description": "Removal of nests"
                    },
                    {
                        "id": "commercial_pest",
                        "title": "Commercial Pest 🏢",
                        "description": "Services for offices"
                    },
                    {
                        "id": "other_pest_issues",
                        "title": "Other Pest Issues 🕷️",
                        "description": "Other pest problems"
                    }
                ]
            }
        ],
        # “chatId” must be the full WhatsApp ID (with “@c.us”)
        "chatId": to_chat_id
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return { "error": "non-json response", "status_code": resp.status_code }


# ────────────────────────────────────────────────────────────────────────────────
# In‐memory state management for each flow (“car,” “bedbug,” “mold”)
# ────────────────────────────────────────────────────────────────────────────────
_user_states: dict = {
    "car": {},
    "bedbug": {},
    "mold": {}
}

def get_user_state(flow: str, phone: str) -> dict:
    return _user_states.get(flow, {}).get(phone)

def set_user_state(flow: str, phone: str, state: dict) -> None:
    if flow not in _user_states:
        _user_states[flow] = {}
    _user_states[flow][phone] = state

def clear_user_state(flow: str, phone: str) -> None:
    if flow in _user_states and phone in _user_states[flow]:
        del _user_states[flow][phone]
