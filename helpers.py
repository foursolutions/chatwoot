# helpers.py

import os
import requests

# ────────────────────────────────────────────────────────────────────────────────
# 1msg / WhatsApp configuration
# ────────────────────────────────────────────────────────────────────────────────
API_KEY_WA  = os.environ.get("WHATSAPP_TOKEN", "")   # e.g. "TKNgrBqpmnbDhf9NzyO5uXNgKHoblDCe"
INSTANCE_ID = "VAN388218473"                         # your 1msg instance ID

# ────────────────────────────────────────────────────────────────────────────────
# send_text_message: Sends a plain text message (or an “interactive” payload) via 1msg’s /send endpoint
# ────────────────────────────────────────────────────────────────────────────────
def send_text_message(message_payload: dict) -> dict:
    """
    message_payload should be a dict containing exactly the JSON you would have
    sent to https://api.1msg.io/{INSTANCE_ID}/send.

    For example, for a button‐style interactive or list, you’d construct `message_payload`
    exactly as WhatsApp expects:
      {
        "to": "6587788080",               # plain digits (no “@c.us”)
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": { … }
      }
    or for a simple text:
      {
        "to": "6587788080",
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Hello!" }
      }

    Returns the 1msg API’s JSON response (as a Python dict).
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/send"
    headers = {
        "Content-Type": "application/json",
        "token": API_KEY_WA
    }
    resp = requests.post(url, json=message_payload, headers=headers)
    try:
        return resp.json()
    except:
        return { "error": f"HTTP {resp.status_code}", "text": resp.text }


# ────────────────────────────────────────────────────────────────────────────────
# send_template_message: Sends a pre‐approved template via 1msg’s /sendTemplate endpoint
# ────────────────────────────────────────────────────────────────────────────────
def send_template_message(to: str, template_name: str, template_params: list) -> dict:
    """
    to:            The recipient’s phone number (plain digits, e.g. "6587788080").
    template_name: The exact name of the template (e.g. "main_menu_v2").
    template_params: A list of strings corresponding to all the “{{1}},” “{{2}},” etc.
                     placeholders in your template. Example: ["Alice", "10:00AM"].

    Returns the 1msg API’s JSON response (as a Python dict).
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendTemplate"
    headers = {
        "Content-Type": "application/json",
        "token": API_KEY_WA
    }
    payload = {
        "namespace": os.environ.get("WHATSAPP_NAMESPACE", ""),
        "template": template_name,
        "language": {
            "policy": "deterministic",
            "code": "en"
        },
        "params": [
            {
                "type": "body",
                "parameters": [
                    { "type": "text", "text": param }
                    for param in template_params
                ]
            }
        ],
        "phone": to
    }
    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except:
        return { "error": f"HTTP {resp.status_code}", "text": resp.text }


# ────────────────────────────────────────────────────────────────────────────────
# send_list_message: Sends a pre‐approved interactive list using 1msg’s /sendList endpoint
# ────────────────────────────────────────────────────────────────────────────────
def send_list_message(to_chat_id: str) -> dict:
    """
    to_chat_id: full WhatsApp ID (e.g. "6587788080@c.us").
    This helper builds and sends the exact JSON that matches your “pest_control_list”,
    “car_fumigation” list, etc., which have already been pre-approved in 1msg.
    You only need to supply the “to” parameter; the rest of the JSON is baked in.

    Returns the 1msg API’s JSON response (as a Python dict).
    """
    plain_phone = to_chat_id.split("@")[0]
    # Example: we know that “pest_control_list” is a pre-approved list template in 1msg.
    # In your account, make sure the name exactly matches “pest_control_list”.
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendList"
    headers = {
        "Content-Type": "application/json",
        "token": API_KEY_WA
    }
    payload = {
        "to": plain_phone,
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": {
            "type": "list",
            "header": { "type": "text", "text": "Select Pest Control Service" },
            "body":   { "text": "Please select the pest control service you need assistance with:" },
            "footer": { "text": "Tap an option" },
            "action": {
                "button": "Select Service",
                "sections": [
                    {
                        "title": "Pest Control Services",
                        "rows": [
                            { "id": "rodents",         "title": "Rodent Control",        "description": "Mice, rats, etc." },
                            { "id": "ants",            "title": "Ant Control",           "description": "Kitchen ants, etc." },
                            { "id": "cockroaches",     "title": "Cockroach Control",     "description": "Kitchen/bath roaches" },
                            { "id": "bedbug",          "title": "Bedbug Services",       "description": "Home & commercial" },
                            { "id": "termite",         "title": "Termite Services",      "description": "Treatment & prevention" },
                            { "id": "car_fumigation",  "title": "Car Fumigation",        "description": "On-site fumigation" },
                            { "id": "mold",            "title": "Mold Remediation",      "description": "Anti-mold painting" }
                        ]
                    }
                ]
            }
        },
        "chatId": to_chat_id
    }
    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except:
        return { "error": f"HTTP {resp.status_code}", "text": resp.text }


# ────────────────────────────────────────────────────────────────────────────────
# Simple in-memory state storage (Redis or any DB would be better in production)
# ────────────────────────────────────────────────────────────────────────────────
_user_states = { 
    "bedbug": {},
    "car": {},
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
