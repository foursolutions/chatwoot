# begin helpers.py
import os
import json
import requests

# -------------------------------------------------------------------
# Helper to send a plain text message via 1msg:
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
    url = f"{base_url}/messages"
    headers = { "Content-Type": "application/json" }
    params = { "token": api_key }
    response = requests.post(url, params=params, headers=headers, json=payload)
    print("[DEBUG] send_text_message →", response.status_code, response.text)
    return response.json()

# -------------------------------------------------------------------
# Helper to send an interactive (button/list) message via 1msg
# (unchanged).
# -------------------------------------------------------------------
def send_interactive_message(payload):
    """
    payload should be a dict like:
      {
        "to": "6588123456",
        "type": "interactive",
        "interactive": { ... },
        "messaging_product": "whatsapp"
      }
    """
    api_key  = os.environ.get("1MSG_API_KEY")
    base_url = os.environ.get("1MSG_BASE_URL")
    url      = f"{base_url}/messages"
    headers  = { "Content-Type": "application/json" }
    params   = { "token": api_key }
    response = requests.post(url, params=params, headers=headers, json=payload)
    print("[DEBUG] send_interactive_message →", response.status_code, response.text)
    return response.json()

# -------------------------------------------------------------------
# NEW: send_template_message(...) for 1msg “/sendTemplate” calls.
# Matches your existing calls in car_fumigation.py:
#   send_template_message(to, template_name, template_params)
# -------------------------------------------------------------------
def send_template_message(to: str, template_name: str, template_params: list):
    """
    Sends a pre‐approved WhatsApp template via 1msg’s /sendTemplate endpoint.

    Arguments:
      to             – recipient phone number (no "+" sign; e.g. "6581234567")
      template_name  – the template identifier (e.g. "main_menu_v2")
      template_params– a list of strings to fill each {{1}}, {{2}}, etc. placeholder
                        in the template’s body.

    It will assemble the correct JSON:
      {
        "token": "<API_KEY>",
        "namespace": "<NAMESPACE>",
        "template": "<TEMPLATE_NAME>",
        "language": {"policy":"deterministic","code":"<LANG_CODE>"},
        "params": [{"type":"body","parameters":[ { "type":"text","text":"<param1>" }, ... ]}],
        "phone": "<TO_NUMBER>"
      }
    """
    api_key   = os.environ.get("1MSG_API_KEY")
    base_url  = os.environ.get("1MSG_BASE_URL")       # e.g. https://api.1msg.io/VAN123456
    namespace = os.environ.get("1MSG_NAMESPACE")      # e.g. 94d66366_9ec1_43a3_a84c_46039bd33ef5
    lang_code = os.environ.get("1MSG_LANG_CODE", "en")# default to "en" unless overridden

    url = f"{base_url}/sendTemplate"
    headers = { "Content-Type": "application/json" }

    # Build the “body” parameters array. Each placeholder <{1}>, <{2}>, ... becomes a text param.
    body_params = []
    for param in template_params:
        body_params.append({
            "type": "text",
            "text": param
        })

    payload = {
        "token": namespace and api_key or api_key,  # token field
        "namespace": namespace,
        "template": template_name,
        "language": {
            "policy": "deterministic",
            "code": lang_code
        },
        "params": [
            {
                "type": "body",
                "parameters": body_params
            }
        ],
        "phone": to
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"[DEBUG] send_template_message → {response.status_code}, {response.text}")
    return response.json()

# -------------------------------------------------------------------
# In‐memory user state store (unchanged).
# You can replace with Redis if desired in future.
# -------------------------------------------------------------------
_user_states = {
    "car": {},
    "bedbug": {},
    "mold": {}
}

def get_user_state(flow_name, phone_number):
    return _user_states.get(flow_name, {}).get(phone_number)

def set_user_state(flow_name, phone_number, state_obj):
    _user_states.setdefault(flow_name, {})[phone_number] = state_obj

def clear_user_state(flow_name, phone_number):
    if phone_number in _user_states.get(flow_name, {}):
        del _user_states[flow_name][phone_number]
# end helpers.py
