import os
import json
import requests

# Grab from Heroku Config Vars
API_KEY  = os.getenv("1MSG_API_KEY", "").strip()
BASE_URL = os.getenv("1MSG_BASE_URL", "").rstrip("/")  # e.g. "https://api.1msg.io/VAN388218473"

if not API_KEY or not BASE_URL:
    raise EnvironmentError(
        "Missing 1MSG_API_KEY or 1MSG_BASE_URL in environment variables."
    )


def send_message_json(payload: dict) -> dict:
    """
    Low-level helper: POST any WhatsApp payload to 1msg's /send endpoint.
    Returns the JSON response from 1msg.
    """
    url = f"{BASE_URL}/send"
    headers = {
        "Content-Type": "application/json"
    }

    # Always include the "token" key at the top level of the JSON:
    payload_with_token = {**payload, "token": API_KEY}
    try:
        r = requests.post(url, headers=headers, json=payload_with_token, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": f"requests exception: {str(e)}"}


def send_interactive_menu(to_number: str) -> dict:
    """
    Sends a button-style interactive menu to `to_number`
    (expects E.164 format, e.g. "+65887788080").
    Returns the JSON response from 1msg.
    """
    if not to_number.startswith("+"):
        to_number = "+" + to_number

    interactive_payload = {
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "Hi there, thanks for reaching out to Four Solutions! "
                    "I'm Solvia, your fun and friendly chatbot.\n"
                    "How may I help you today? (Tap \"Live Human\" anytime, or choose one of the options below.)"
                )
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "help_pest",
                            "title": "Need help on Pest!"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "help_mold",
                            "title": "Need help on Mold!"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "live_human",
                            "title": "Live Human"
                        }
                    }
                ]
            }
        },
        "messaging_product": "whatsapp"
    }

    return send_message_json(interactive_payload)


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


def get_user_state(flow: str, user: str) -> dict:
    """
    Placeholder: fetch user state from Redis (or wherever).
    Implement as needed.
    """
    # Example stub—you may replace with real Redis logic.
    return {}


def set_user_state(flow: str, user: str, state: dict) -> None:
    """
    Placeholder: store user state in Redis (or wherever).
    Implement as needed.
    """
    pass


def clear_user_state(flow: str, user: str) -> None:
    """
    Placeholder: delete user state from Redis (or wherever).
    Implement as needed.
    """
    pass
