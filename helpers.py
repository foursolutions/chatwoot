# helpers.py (cleaned up)

import os
import json
import requests
import redis

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

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


def send_template_message(to: str, template_name: str, template_params=None):
    if template_params is None:
        template_params = []

    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }

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

    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()


def send_interactive_message(payload: dict):
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }

    payload.setdefault("messaging_product", "whatsapp")
    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()


def send_text_message(to: str, body: str):
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
