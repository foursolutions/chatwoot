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
        "to": "6588123456",            # digits only
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
        return {"error": "Invalid JSON response from 1msg"}


# -------------------------------------------------------------------
# Helper to send an interactive (button/list) message via 1msg
# -------------------------------------------------------------------
def send_interactive_message(payload):
    """
    payload should be a dict like one of:
    (A) Sending a button or list or template:
      {
        "to": "6588123456",    # digits only
        "type": "interactive",
        "messaging_product": "whatsapp",
        "interactive": { … }
      }
    (B) Sending a WhatsApp‐template via 1msg's /sendTemplate endpoint:
      {
        "token":    "<API_KEY>",
        "namespace": "<NAMESPACE>",
        "template":  "main_menu_v2",
        "language":  {"policy": "deterministic", "code": "en"},
        "params": [
          {
            "type": "body",
            "parameters": [{"type": "text", "text": "…"}]
          }
        ],
        "phone": "6588123456"   # digits only
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
        return {"error": "Invalid JSON response from 1msg"}


# -------------------------------------------------------------------
# Helper to send a WhatsApp‐template (preapproved) message via 1msg
# -------------------------------------------------------------------
def send_template_message(to: str, template_name: str, template_params: list):
    """
    to            : recipient’s phone number (digits only), e.g. "6588123456"
    template_name : the exact name of your WhatsApp template, e.g. "main_menu_v2"
    template_params: a list of strings for each placeholder in that template’s body
    """
    api_key   = os.environ.get("1MSG_API_KEY")
    namespace = os.environ.get("1MSG_NAMESPACE")  # configured in Heroku config vars
    url       = f"{os.environ.get('1MSG_BASE_URL')}/sendTemplate"

    # Build the 1msg /sendTemplate payload:
    payload = {
        "token":     api_key,
        "namespace": namespace,
        "template":  template_name,
        "language":  {"policy": "deterministic", "code": "en"},
        "params": [
            {
                "type":       "body",
                "parameters": [{"type": "text", "text": param} for param in template_params]
            }
        ],
        "phone": to  # MUST be digits-only
    }

    print("[DEBUG] 1msg SEND TEMPLATE payload:", json.dumps(payload, indent=2))
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
    print(f"[DEBUG] send_template_message → {response.status_code}, {response.text}")
    try:
        return response.json()
    except ValueError:
        return {"error": "Invalid JSON response from 1msg"}


# -------------------------------------------------------------------
# In-memory user-state store
# -------------------------------------------------------------------
_user_states = {
    "car":    {},
    "bedbug": {},
    "mold":   {}
}

def get_user_state(flow_name: str, phone_number: str):
    """
    Return the stored state dict (or None if not found).
    """
    return _user_states.get(flow_name, {}).get(phone_number)

def set_user_state(flow_name: str, phone_number: str, state_obj: dict):
    """
    Store the given state_obj (a dict) under (flow_name, phone_number).
    """
    _user_states.setdefault(flow_name, {})[phone_number] = state_obj

def clear_user_state(flow_name: str, phone_number: str):
    """
    Remove any stored state for (flow_name, phone_number).
    """
    if phone_number in _user_states.get(flow_name, {}):
        del _user_states[flow_name][phone_number]
