# helpers.py
import os
import requests

# ——————————————  
# 1) Load environment variables
# ——————————————
API_KEY  = os.getenv("1MSG_API_KEY", "").strip()
BASE_URL = os.getenv("1MSG_BASE_URL", "").rstrip("/")  # e.g. "https://api.1msg.io/VAN388218473"

if not API_KEY or not BASE_URL:
    raise EnvironmentError(
        "Missing 1MSG_API_KEY or 1MSG_BASE_URL in environment variables."
    )


# ——————————————  
# 2) Low-level send to the 1MSG “/message” endpoint
# ——————————————
def send_message_json(payload: dict) -> dict:
    """
    Low-level helper: POST any WhatsApp payload to 1msg's /message endpoint.
    Returns the JSON response or an {"error": ...} dict on failure.
    """
    url = f"{BASE_URL}/message"            # <— Note: /message, not /send
    headers = {"Content-Type": "application/json"}
    payload_with_token = {**payload, "token": API_KEY}

    try:
        r = requests.post(url, headers=headers, json=payload_with_token, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": f"requests exception: {str(e)}"}


# ——————————————  
# 3) Plain text message
# ——————————————
def send_text_message(to_number: str, text: str) -> dict:
    """
    Sends a plain text message to `to_number`.
    Returns the JSON response from 1msg.
    """
    if not to_number.startswith("+"):
        to_number = "+" + to_number

    payload = {
        "to": to_number,
        "type": "text",
        "text": {"body": text},
        "messaging_product": "whatsapp"
    }
    return send_message_json(payload)


# ——————————————  
# 4) Interactive message (buttons / lists)
# ——————————————
def send_interactive_message(interactive_payload: dict) -> dict:
    """
    Sends an interactive‐style payload (button or list).
    Caller must include “to”, “messaging_product”: “whatsapp”, and the correct “interactive” block.
    """
    return send_message_json(interactive_payload)


# ——————————————  
# 5) Template message
# ——————————————
def send_template_message(to: str, template_name: str, template_params: list) -> dict:
    """
    Sends a template message via 1MSG.
    Example payload shape (adjust based on your 1MSG template setup):
      {
        "to": "+6588662359",
        "type": "template",
        "template": {
           "name": "main_menu_v2",
           "language": {"policy": "deterministic", "code": "en"},
           "components": [
             {"type": "body", "parameters": [ {"type": "text", "text": "Alice"} ] }
           ]
        },
        "messaging_product": "whatsapp"
      }
    """
    if not to.startswith("+"):
        to = "+" + to

    body_params = []
    for s in template_params:
        body_params.append({"type": "text", "text": str(s)})

    payload = {
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"policy": "deterministic", "code": "en"},
            "components": [
                {"type": "body", "parameters": body_params}
            ]
        },
        "messaging_product": "whatsapp"
    }
    return send_message_json(payload)


# ——————————————  
# 6) Stubbed Redis “state” helpers
# ——————————————
def get_user_state(flow: str, user: str) -> dict:
    """
    Placeholder: fetch user state from Redis (or wherever).
    """
    return {}


def set_user_state(flow: str, user: str, state: dict) -> None:
    """
    Placeholder: store user state in Redis (or wherever).
    """
    pass


def clear_user_state(flow: str, user: str) -> None:
    """
    Placeholder: delete user state from Redis (or wherever).
    """
    pass
