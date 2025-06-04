# helpers.py

import os
import redis
import json
import requests

# ============================
#  Configuration (unchanged)
# ============================
# These two must be defined in your Heroku Config Vars:
#
#   1MSG_API_KEY   = TKNgRBqpmnDbRf9NzyO5uXNgKHobiDCe
#   1MSG_BASE_URL  = https://api.1msg.io/VAN388218473/
#
# (No longer using WHATSAPP_TOKEN / D360‐API‐KEY)
API_KEY    = os.getenv("1MSG_API_KEY")
BASE_URL   = os.getenv("1MSG_BASE_URL", "").rstrip("/")  # e.g. "https://api.1msg.io/VAN388218473"
REDIS_URL  = os.getenv("REDIS_URL")

if not API_KEY or not BASE_URL:
    raise RuntimeError("Missing 1MSG_API_KEY or 1MSG_BASE_URL in environment variables.")

# Initialize Redis client (unchanged)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# ===================================
#  Redis‐based State Functions (unchanged)
# ===================================
def get_user_state(prefix: str, user_id: str) -> dict:
    key = f"{prefix}:{user_id}"
    raw = r.get(key)
    return json.loads(raw) if raw else {}


def set_user_state(prefix: str, user_id: str, state: dict):
    key = f"{prefix}:{user_id}"
    r.set(key, json.dumps(state), ex=3600)


def clear_user_state(prefix: str, user_id: str):
    key = f"{prefix}:{user_id}"
    r.delete(key)


# =====================================================
#  1msg “send”‐Endpoint Helper (replaces 360dialog V2)
# =====================================================
def _post_to_1msg(payload: dict) -> dict:
    """
    Internal helper: POST the given JSON payload to 1msg’s /send endpoint.
    Headers must include x-api-key: <your 1MSG_API_KEY>.
    """
    url = f"{BASE_URL}/send"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ======================================================
#  send_template_message (via 1msg, forwarding 360dialog)
# ======================================================
def send_template_message(to: str, template_name: str, template_params=None):
    """
    Sends a WhatsApp template message through 1msg. 1msg will forward to 360dialog.
    
    - to: recipient phone number (e.g. "6591234567")
    - template_name: exact name of the approved template in 360dialog
    - template_params: list of strings to fill {{1}}, {{2}}, ... in the template body
    """
    if template_params is None:
        template_params = []

    # Build “body” parameters exactly as we used to for 360dialog
    body_parameters = [{"type": "text", "text": param} for param in template_params]

    payload = {
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": { "code": "en" },
            "components": [
                {
                    "type": "body",
                    "parameters": body_parameters
                }
            ]
        },
        "messaging_product": "whatsapp"
    }

    return _post_to_1msg(payload)


# ===============================================================
#  send_interactive_message (via 1msg, forwarding 360dialog “interactive”)
# ===============================================================
def send_interactive_message(payload: dict):
    """
    Sends a “session‐based” interactive message (list or quick‐reply) via 1msg.
    You must include "messaging_product": "whatsapp" at the top level of payload.
    """
    # Ensure “messaging_product” is always set to "whatsapp"
    payload.setdefault("messaging_product", "whatsapp")
    return _post_to_1msg(payload)


# ================================================================
#  send_text_message (via 1msg, forwarding 360dialog “text”)
# ================================================================
def send_text_message(to: str, body: str):
    """
    Sends a simple text message (non‐template) via 1msg.
    Must include "messaging_product": "whatsapp" as well.
    """
    payload = {
        "to": to,
        "type": "text",
        "text": { "body": body },
        "messaging_product": "whatsapp"
    }
    return _post_to_1msg(payload)
