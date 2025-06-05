# begin helpers.py
import os
import json
import requests

# Helper to send a plain text message via 1msg:
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
    headers = {
        "Content-Type": "application/json"
    }
    params = { "token": api_key }
    response = requests.post(url, params=params, headers=headers, json=payload)
    print("[DEBUG] send_text_message →", response.status_code, response.text)
    return response.json()

# Helper to send an interactive (button/list) message via 1msg:
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

# New helper to send a template message via 1msg:
def send_template_message(to: str, template_name: str, template_params: list):
    """
    to: phone number in international format (no leading '+'), e.g. "6588123456"
    template_name: the exact name of your WhatsApp template (e.g. "main_menu_v2")
    template_params: a list of strings, one for each body placeholder (e.g. ["Alice"])
    """
    api_key   = os.environ.get("1MSG_API_KEY")
    base_url  = os.environ.get("1MSG_BASE_URL")      # e.g. https://api.1msg.io/VAN123456
    namespace = os.environ.get("1MSG_NAMESPACE")     # e.g. 94d66366_9ec1_43a3_a84c_46039bd33ef5
    lang_code = os.environ.get("1MSG_LANG_CODE", "en")  # e.g. "en"

    url = f"{base_url}/sendTemplate"
    headers = { "Content-Type": "application/json" }

    # Build the body parameters array: one entry per placeholder in the template
    body_parameters = []
    for text in template_params:
        body_parameters.append({ "type": "text", "text": text })

    payload = {
        "token":     api_key,
        "namespace": namespace,
        "template":  template_name,
        "language": {
            "policy": "deterministic",
            "code":   lang_code
        },
        "params": [
            {
                "type":       "body",
                "parameters": body_parameters
            }
        ],
        "phone": to
    }

    # <<< DEBUG PRINT: show exactly what we are sending to 1msg >>>
    print("[DEBUG] 1msg SEND TEMPLATE payload:\n", json.dumps(payload, indent=2))

    response = requests.post(url, headers=headers, json=payload)
    print("[DEBUG] send_template_message →", response.status_code, response.text)
    return response.json()


# In‐memory user state store (you can replace with Redis if desired):
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
