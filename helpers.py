# helpers.py

import os
import requests

# ─── Read from your Heroku Config Vars ──────────────────
API_KEY_1MSG    = os.getenv("1MSG_API_KEY", "").strip()
BASE_URL_1MSG   = os.getenv("1MSG_BASE_URL", "").rstrip("/")      # e.g. "https://api.1msg.io/VAN388218473"
NAMESPACE_1MSG  = os.getenv("1MSG_NAMESPACE", "").strip()         # e.g. "94d66366_9ec1_43a3_a84c_46039bd33ef5"
LANG_CODE_1MSG  = os.getenv("1MSG_LANG_CODE", "en").strip()       # e.g. "en"
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2").strip()
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "").strip()        # e.g. "66681799847695"

# ─── 1) send_text_message: wraps /sendMessage for plain text ──
def send_text_message(message_payload: dict) -> dict:
    """
    Sends a plain-text WhatsApp message via 1msg's /sendMessage endpoint.
    Expect message_payload to look like:
      {
        "to": "6591234567",
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Your text here" }
      }
    """
    url = f"{BASE_URL_1MSG}/sendMessage"
    headers = {
        "Content-Type": "application/json",
        "token": API_KEY_1MSG
    }
    resp = requests.post(url, json=message_payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non-JSON response: {resp.text}"}


# ─── 2) send_template_message: wraps /sendTemplate ─────────────
def send_template_message(
    to: str,
    template_name: str,
    template_params: list[str] = None,
    language_code: str = LANG_CODE_1MSG,
    policy: str = "deterministic"
) -> dict:
    """
    Sends a pre-approved WhatsApp Template via 1msg's /sendTemplate endpoint.

    to             = phone number (digits only, e.g. "6591234567")
    template_name  = the exact name of the approved template, e.g. "main_menu_v2"
    template_params= a list of body parameters, e.g. ["Solvia"] if your template needs 1 body param
    """
    if template_params is None:
        template_params = []

    # Build the 'params' structure properly with a list comprehension:
    params_body = {
        "type": "body",
        "parameters": [
            {"type": "text", "text": p}
            for p in template_params
        ],
    }

    url = f"{BASE_URL_1MSG}/sendTemplate"
    headers = {
        "Content-Type": "application/json",
        "token": API_KEY_1MSG
    }
    payload = {
        "namespace": NAMESPACE_1MSG,
        "template": template_name,
        "language": {"policy": policy, "code": language_code},
        "params": [params_body],
        "phone": to
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non-JSON response: {resp.text}"}


# ─── 3) send_list_message: wraps /sendList ───────────────────────
def send_list_message(
    to: str,
    body: str,
    header: str,
    footer: str,
    action_title: str,
    sections: list[dict]
) -> dict:
    """
    Sends an interactive LIST via 1msg's /sendList endpoint.

    to           = phone number (digits only)
    body         = the 'body.text' field for the list
    header       = header text (or empty string if none)
    footer       = footer text (or empty string if none)
    action_title = the 'action.button' label, e.g. "Select Service"
    sections     = a list of { "title": "...", "rows": [ {"id": "...","title":"...","description":"..."} , ... ] }

    Example 'sections' argument:
      [
        {
          "title": "Common Pest Issues",
          "rows": [
            {
              "id": "car_fumigation",
              "title": "Car Fumigation 🚗",
              "description": "On-site fumigation & fogging"
            },
            ...
          ]
        }
      ]
    """
    url = f"{BASE_URL_1MSG}/sendList"
    headers = {
        "Content-Type": "application/json",
        "token": API_KEY_1MSG
    }
    payload = {
        "body":   body,
        "header": header,
        "footer": footer,
        "action": action_title,
        "sections": sections,
        "chatId": to
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non-JSON response: {resp.text}"}

