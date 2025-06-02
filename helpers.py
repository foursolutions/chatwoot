# helpers.py

import os
import requests
import redis
import json

# ============
# Configuration
# ============
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

# Initialize Redis client
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

# ===========================
# Redis‐based State Functions
# ===========================
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


# ===================================
# 360dialog V2 HTTP‐Request Functions
# ===================================
def send_template_message(to: str, template_name: str, template_params=None):
    """
    Sends a WhatsApp template message via 360dialog V2.
    - to: recipient phone number (e.g., "6591234567")
    - template_name: exact name of the approved template in 360dialog
    - template_params: list of strings to fill {{1}}, {{2}}, ... in the template body
    """
    if template_params is None:
        template_params = []

    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }

    # Build parameters array for the "body" component
    body_parameters = [{"type": "text", "text": param} for param in template_params]

    payload = {
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": { "code": "en" },   # <-- Use "en" (not "en_US")
            "components": [
                {
                    "type": "body",
                    "parameters": body_parameters
                }
            ]
        },
        "messaging_product": "whatsapp"
    }

    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()


def send_interactive_message(payload: dict):
    """
    Sends a “session‐based” interactive message (list or quick‐reply) via 360dialog V2.
    Must include "messaging_product": "whatsapp" at the top level of payload.
    """
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }

    payload.setdefault("messaging_product", "whatsapp")
    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()


def send_text_message(to: str, body: str):
    """
    Sends a simple text message (non‐template) via 360dialog V2.
    Must include "messaging_product": "whatsapp" as well.
    """
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "to": to,
        "type": "text",
        "text": { "body": body },
        "messaging_product": "whatsapp"
    }

    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()
