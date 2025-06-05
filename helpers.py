# helpers.py

import os
import json
import requests

# -------------------------------------------------------------------
# Helper to send a plain text message via 1msg
# -------------------------------------------------------------------
def send_text_message(payload):
    """
    payload should be a dict like:
      {
        "to": "6588123456",
        "type": "text",
        "text": {"body": "Hello!"},
        "messaging_product": "whatsapp"
      }
    """
    api_key  = os.environ.get("1MSG_API_KEY")
    base_url = os.environ.get("1MSG_BASE_URL")  # e.g. https://api.1msg.io/VAN123456
    url      = f"{base_url}/messages"
    headers  = { "Content-Type": "application/json" }
    params   = { "token": api_key }
    response = requests.post(url, params=params, headers=headers, json=payload)
    print(f"[DEBUG] send_text_message → {response.status_code}, {response.text}")
    try:
        return response.json()
    except ValueError:
        return { "error": "Invalid JSON response from 1msg" }

# -------------------------------------------------------------------
# Helper to send an interactive (button/list) message via 1msg
# -------------------------------------------------------------------
def send_interactive_message(payload):
    """
    payload should be a dict like:
      {
        "to": "6588123456",
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": { ... }
      }
    """
    api_key  = os.environ.get("1MSG_API_KEY")
    base_url = os.environ.get("1MSG_BASE_URL")
    url      = f"{base_url}/messages"
    headers  = { "Content-Type": "application/json" }
    params   = { "token": api_key }
    response = requests.post(url, params=params, headers=headers, json=payload)
    print(f"[DEBUG] send_interactive_message → {response.status_code}, {response.text}")
    try:
        return response.json()
    except ValueError:
        return { "error": "Invalid JSON response from 1msg" }

# -------------------------------------------------------------------
# Helper to send a WhatsApp‐template (preapproved) message via 1msg
# -------------------------------------------------------------------
def send_template_message(to: str, template_name: str, template_params: list):
    """
    to            : recipient’s phone number in full international format (no “+” or spaces), e.g. "6588123456"
    template_name : the exact name of your WhatsApp template (e.g. "main_menu_v2")
    template_params: a list of strings for each placeholder in your template’s body
    """
    api_key   = os.environ.get("1MSG_API_KEY")
    namespace = os.environ.get("1MSG_NAMESPACE")    # must be set in Heroku’s config vars
    url       = f"{os.environ.get('1MSG_BASE_URL')}/sendTemplate"

    payload = {
        "token":    api_key,
        "namespace": namespace,
        "template":  template_name,
        "language":  { "policy": "deterministic", "code": "en" },
        "params": [
            {
                "type":       "body",
                "parameters": [{ "type": "text", "text": param } for param in template_params]
            }
        ],
        "phone": to
    }

    print("[DEBUG] 1msg SEND TEMPLATE payload:", json.dumps(payload, indent=2))
    response = requests.post(url, headers={ "Content-Type": "application/json" }, json=payload)
    print(f"[DEBUG] send_template_message → {response.status_code}, {response.text}")
    try:
        return response.json()
    except ValueError:
        return { "error": "Invalid JSON response from 1msg" }

# -------------------------------------------------------------------
# In‐memory user‐state store (can be swapped out for Redis if desired)
# -------------------------------------------------------------------
_user_states = {
    "car":    {},
    "bedbug": {},
    "mold":   {}
}

def get_user_state(flow_name: str, phone_number: str):
    return _user_states.get(flow_name, {}).get(phone_number)

def set_user_state(flow_name: str, phone_number: str, state_obj: dict):
    _user_states.setdefault(flow_name, {})[phone_number] = state_obj

def clear_user_state(flow_name: str, phone_number: str):
    if phone_number in _user_states.get(flow_name, {}):
        del _user_states[flow_name][phone_number]
