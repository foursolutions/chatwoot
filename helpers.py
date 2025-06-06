# helpers.py

import os
import requests

# ─── Read from your Heroku Config Vars ────────────────────────────────────────

# API key for 1msg (Config Var “1MSG_API_KEY”)
API_KEY_1MSG = os.getenv("1MSG_API_KEY", "").strip()

# Base URL for 1msg (Config Var “1MSG_BASE_URL”), e.g. "https://api.1msg.io/VAN388218473"
BASE_URL_1MSG = os.getenv("1MSG_BASE_URL", "").rstrip("/")

# Namespace for approved templates (Config Var “1MSG_NAMESPACE”)
NAMESPACE_1MSG = os.getenv("1MSG_NAMESPACE", "").strip()

# Default language code (Config Var “1MSG_LANG_CODE”), typically "en"
LANG_CODE_1MSG = os.getenv("1MSG_LANG_CODE", "en").strip()


# ─── 1) send_template_message ─────────────────────────────────────────────────

def send_template_message(
    to: str,
    template_name: str,
    template_params: list[str]
) -> dict:
    """
    Sends a WhatsApp Template message (using 1msg's /sendTemplate endpoint).

    - `to` must be digits only, e.g. "6587788080" (no "@c.us").
    - `template_name` must be exactly your approved template name, e.g. "main_menu_v2".
    - `template_params` is a list of body-parameters. If your template has one placeholder,
      you might pass ["there"].
    """
    url = f"{BASE_URL_1MSG}/sendTemplate"
    headers = {"Content-Type": "application/json"}

    # Build the "params" block (body parameters) exactly as 1msg expects:
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
        "token": API_KEY_1MSG,
        "namespace": NAMESPACE_1MSG,
        "template": template_name,
        "language": {
            "policy": "deterministic",
            "code": LANG_CODE_1MSG
        },
        "params": params_block,
        "phone": to   # digits only, e.g. "6587788080"
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non‐JSON response: {resp.text}"}


# ─── 2) send_list_message ─────────────────────────────────────────────────────

def send_list_message(
    to: str,
    header: str,
    body: str,
    footer: str,
    action_button_label: str,
    sections: list[dict]
) -> dict:
    """
    Sends an interactive LIST via 1msg’s /sendList endpoint.

    - `to` must be digits only (e.g. "6587788080").
    - `header`, `body`, `footer`, `action_button_label` are strings.
    - `sections` is a list of dicts; each dict represents one section of rows. For example:

        sections = [
          {
            "title": "My Section Title",
            "rows": [
              {
                "id": "row_id_1",
                "title": "Row Title 1",
                "description": "Row Description 1"
              },
              { ... }
            ]
          },
          { ... }
        ]
    """
    url = f"{BASE_URL_1MSG}/sendList"
    headers = {"Content-Type": "application/json"}

    payload = {
        "token": API_KEY_1MSG,
        "body": body,                    # the main body text of the list
        "header": header,                # header text
        "footer": footer,                # footer text
        "action": action_button_label,   # the button label ("Select …")
        "sections": sections,
        "chatId": to                     # digits only, e.g. "6587788080"
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non‐JSON response: {resp.text}"}


# ─── 3) Helpers for sending plain text ────────────────────────────────────────

def send_text_message(message_payload: dict) -> dict:
    """
    A convenience wrapper for sending a plain text message.
    Expects a payload of the form:
      {
        "to": "6587788080",
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Hello!" }
      }
    You can call:
      send_text_message({
          "to": "6587788080",
          "type": "text",
          "messaging_product": "whatsapp",
          "text": { "body": "Your message here" }
      })
    """
    url = f"{BASE_URL_1MSG}/sendMessage"
    headers = {"Content-Type": "application/json", "token": API_KEY_1MSG}
    resp = requests.post(url, json=message_payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non‐JSON response: {resp.text}"}
