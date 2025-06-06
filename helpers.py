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
    message_payload should be a dict in this shape:
      {
        "to": "<countrycode><phone_no>",
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "<your text here>" }
      }
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/send"
    headers = {"Content-Type": "application/json"}
    # Add the token automatically:
    final_payload = {
        **message_payload,
        "token": API_KEY_WA
    }
    resp = requests.post(url, json=final_payload, headers=headers)
    try:
        return resp.json()
    except:
        return {"error": f"non-JSON response: {resp.text}"}

# ────────────────────────────────────────────────────────────────────────────────
# send_template_message: Sends a WhatsApp Template via 1msg’s /sendTemplate
# ────────────────────────────────────────────────────────────────────────────────
def send_template_message(
    to: str,
    template_name: str,
    template_params: list[str],
    language_code: str = "en",
    policy: str = "deterministic"
) -> dict:
    """
    to:               phone number (digits only; e.g. "6591234567")
    template_name:    the name of your approved template, e.g. "main_menu_v2"
    template_params:  e.g. ["there"] if your template has one body parameter
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendTemplate"
    headers = {"Content-Type": "application/json"}

    # Build the "params" structure correctly using a list‐comprehension:
    params_block = [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": param}
                for param in template_params
            ]
        }
    ]

    payload = {
        "token": API_KEY_WA,
        "namespace": os.getenv("WHATSAPP_NAMESPACE", ""),  # e.g. "94d66366_9ec1_43a3_a84c_46039bd33ef5"
        "template": template_name,
        "language": {
            "policy": policy,
            "code": language_code
        },
        "params": params_block,
        "phone": to
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except:
        return {"error": f"non-JSON response: {resp.text}"}


# ────────────────────────────────────────────────────────────────────────────────
# send_list_message: Sends a WhatsApp interactive list via 1msg’s /sendList
# ────────────────────────────────────────────────────────────────────────────────
def send_list_message(
    to: str,
    body: str,
    header: str,
    footer: str,
    action_button: str,
    sections: list[dict]
) -> dict:
    """
    to:             the WhatsApp chatId (e.g. "6591234567@c.us") or just "6591234567"
    body:           message body (string; can be blank or short)
    header:         top-line text for the interactive list
    footer:         bottom-line text for the interactive list
    action_button:  the button label, e.g. "Select Option"
    sections:       a list of section dicts, each of form:
                      {
                        "title": "Section Title",
                        "rows": [
                           {"id": "item_id_1", "title": "Human-readable Title 1", "description": "…"},
                           …
                        ]
                      }
    """
    url = f"https://api.1msg.io/{INSTANCE_ID}/sendList"
    headers = {"Content-Type": "application/json"}

    # If the user passed e.g. "6591234567" instead of "6591234567@c.us", normalize:
    if not to.endswith("@c.us"):
        to = f"{to}@c.us"

    payload = {
        "token": API_KEY_WA,
        "body": body,
        "header": header,
        "footer": footer,
        "action": action_button,
        "sections": sections,
        "chatId": to
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except:
        return {"error": f"non-JSON response: {resp.text}"}


# ────────────────────────────────────────────────────────────────────────────────
# In-memory ephemeral state store (per-user, per-flow). Feel free to swap out
# for Redis or anything else in prod; this is just an example.
# ────────────────────────────────────────────────────────────────────────────────
_user_states: dict[str, dict[str, dict]] = {
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
