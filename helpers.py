# helpers.py

import os
import json
import requests
import redis

# ============
# Configuration
# ============
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE")
REDIS_URL = os.getenv("REDIS_URL")

# Initialize Redis client (decode_responses=True for string I/O)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

# ===========================
# Redis‐based State Functions
# ===========================
def get_user_state(prefix: str, user_id: str) -> dict:
    """
    Fetches the JSON‐encoded state dict from Redis under key "<prefix>:<user_id>".
    Returns an empty dict if no state is present.
    """
    key = f"{prefix}:{user_id}"
    raw = r.get(key)
    return json.loads(raw) if raw else {}

def set_user_state(prefix: str, user_id: str, state: dict):
    """
    Stores the JSON‐encoded `state` dict under key "<prefix>:<user_id>"
    with a TTL of 1 hour.
    """
    key = f"{prefix}:{user_id}"
    r.set(key, json.dumps(state), ex=3600)

def clear_user_state(prefix: str, user_id: str):
    """
    Deletes the Redis key "<prefix>:<user_id>".
    """
    key = f"{prefix}:{user_id}"
    r.delete(key)

# ===================================
# 360dialog/Meta HTTP‐Request Functions
# ===================================
def send_template_message(to_phone: str, template_name: str, template_params=None):
    """
    Sends a WhatsApp template message via 360dialog.
    - to_phone: recipient phone number (e.g. "6591234567")
    - template_name: exact name of the approved template in 360dialog
    - template_params: list of strings that fill {{1}}, {{2}}, ... in the template body
    """
    if template_params is None:
        template_params = []

    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    body = {
        "to": to_phone,
        "type": "template",
        "template": {
            "namespace": TEMPLATE_NAMESPACE,
            "name": template_name,
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": param}
                        for param in template_params
                    ]
                }
            ]
        }
    }

    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code not in (200, 201):
        print(f"[send_template_message] Error {resp.status_code}: {resp.text}")
    return resp.json()

def send_interactive_message(payload: dict):
    """
    Sends a “session‐based” interactive message (list or quick‐reply) via 360dialog.
    The payload must include at least:
      {
        "to": "<PHONE_NUMBER>",
        "type": "interactive",
        "interactive": { ... }
      }
    """
    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        print(f"[send_interactive_message] Error {resp.status_code}: {resp.text}")
    return resp.json()

def send_text_message(to: str, body: str):
    """
    Sends a simple text message (non‐template) via 360dialog. Allowed if user messaged within 24h.
    """
    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        print(f"[send_text_message] Error {resp.status_code}: {resp.text}")
    return resp.json()

