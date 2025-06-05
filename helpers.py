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
    message_payload should already include:
      {
        "to": "<chatId>",         # e.g. "6587788080@c.us"
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Hello!" }
      }
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/send"
    headers = { "Content-Type": "application/json" }
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
    to: the chatId (e.g. "6587788080@c.us")
    template_name: name of your approved template (e.g. "main_menu_v2")
    template_params: list of strings for body-placeholders
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendTemplate"
    headers = { "Content-Type": "application/json" }

    # Build the “params” array for the template
    params_array = []
    if template_params:
        # Example structure:
        # "params": [
        #   { "type": "body", "parameters": [ { "type": "text", "text": "<param1>" } ] },
        #   { "type": "body", "parameters": [ { "type": "text", "text": "<param2>" } ] }
        # ]
        for p in template_params:
            params_array.append({
                "type": "body",
                "parameters": [
                    { "type": "text", "text": p }
                ]
            })

    payload = {
        "token": API_KEY_WA,
        "namespace": os.environ.get("WHATSAPP_NAMESPACE", ""),  # If you use a namespace, otherwise omit or set blank
        "template": template_name,
        "language": { "policy": "deterministic", "code": "en" },
        "params": params_array,
        "phone": to.replace("@c.us", "")  # 1msg expects phone without “@c.us”
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return { "error": "non-json response", "status_code": resp.status_code }


# ────────────────────────────────────────────────────────────────────────────────
# send_interactive_message (retained for backwards compatibility, if needed)
# ────────────────────────────────────────────────────────────────────────────────
def send_interactive_message(payload: dict) -> dict:
    """
    payload: free-form interactive JSON. This will be silently dropped by WhatsApp
             if it’s a “list” that isn’t pre-approved—use send_list_message instead.
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/send"
    headers = { "Content-Type": "application/json" }
    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return { "error": "non-json response", "status_code": resp.status_code }


# ────────────────────────────────────────────────────────────────────────────────
# send_list_message: Uses the 1msg “/sendList” endpoint to send a fully-supported
#                    WhatsApp "interactive list" (pest control menu) that won’t vanish.
# ────────────────────────────────────────────────────────────────────────────────
def send_list_message(to_chat_id: str) -> dict:
    """
    to_chat_id must be the full WhatsApp ID, e.g. "6587788080@c.us".
    Returns the JSON response from 1msg.
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendList"
    headers = { "Content-Type": "application/json" }

    payload = {
        "token": API_KEY_WA,
        # ────── The “body” text that appears above the list rows ──────
        "body":   "Please select the pest control service you need assistance with:\n",
        # ────── The “header” text at the very top ──────
        "header": "Pest Control Services",
        # ────── The “footer” text at the bottom ──────
        "footer": "Tap to choose",
        # ────── The button label that opens the list ──────
        "action": "Select Service",
        # ────── Exactly one section called “Common Pest Issues” with its rows ──────
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
        # ────── “chatId” must be the full WhatsApp ID (with “@c.us”) ──────
        "chatId": to_chat_id
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return { "error": "non-json response", "status_code": resp.status_code }


# ────────────────────────────────────────────────────────────────────────────────
# In-Memory State Helpers (unchanged)
# ────────────────────────────────────────────────────────────────────────────────

_user_states: dict = {
    # Structure: { "<flow_name>": { "<phone>": { ... state ... } } }
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
