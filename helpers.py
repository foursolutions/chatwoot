# helpers.py

import os
import json
import requests

# -----------------------------------------------------------------------------
# This file contains three kinds of helper functions:
#   • send_text_message(...)
#   • send_template_message(...)
#   • clear/set/get user state (via Redis)
# -----------------------------------------------------------------------------

#
# 1) TEXT‐ONLY MESSAGE
#
def send_text_message(to: str, text: str):
    """
    Send a plain "text" message over 1MSG.  For WhatsApp, text must be a simple string.
    """
    API_KEY    = os.environ["1MSG_API_KEY"]
    BASE_URL   = os.environ["1MSG_BASE_URL"].rstrip("/")  # e.g. "https://api.1msg.io/VAN12345678"
    PHONE_ID   = os.environ.get("PHONE_NUMBER_ID", None)   # (for WhatsApp business channel push)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "token": API_KEY,
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {
            "body": text
        }
    }
    # If you also need phone_number_id in the 1MSG payload, you can add it here:
    if PHONE_ID:
        payload["phone_number_id"] = PHONE_ID

    url = f"{BASE_URL}/messages"
    resp = requests.post(url, headers=headers, json=payload)
    # Debug log
    print(f"[DEBUG] send_text_message → {resp.status_code}, {resp.text}")
    return resp.json()


#
# 2) TEMPLATE MESSAGE (buttons, interactive, etc.)
#
def send_template_message(to: str, token: str, template_name: str, language: dict, params: list):
    """
    Send a template message via 1MSG.  We no longer pass `namespace` here as a separate keyword
    (the 1MSG API already knows your namespace by virtue of the VAN ID in BASE_URL).
    - `to`           : recipient phone (E.164 without '+', e.g. "6588601234")
    - `token`        : same as 1MSG_API_KEY
    - `template_name`: name of your template, e.g. "main_menu_v2"
    - `language`     : {"policy": "deterministic", "code": "en"}
    - `params`       : list of body/header/button parameters (JSON‐serializable)
    """
    BASE_URL = os.environ["1MSG_BASE_URL"].rstrip("/")  # e.g. "https://api.1msg.io/VAN388218473"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "token": token,
        "template": template_name,
        "language": language,
        "params": params,
        "phone": to
    }

    url = f"{BASE_URL}/sendTemplate"
    resp = requests.post(url, headers=headers, json=payload)
    print(f"[DEBUG] send_template_message → {resp.status_code}, {resp.text}")
    return resp.json()


#
# 3) SIMPLE KEY‐VALUE STATE STORAGE (using Redis)
#
#    We store per‐user “state” under keys like "car:{from_number}".
#    You can tweak these helpers if you use a different Redis library.
#
import redis

# Parse Redis connection string from environment.  This might be something like
#   REDIS_URL="redis://:<password>@<hostname>:<port>"
# You already have REDIS_URL set in Heroku config.
redis_conn = redis.from_url(os.environ.get("REDIS_URL", ""), decode_responses=True)


def get_user_state(flow: str, user_id: str) -> dict:
    """
    Read a JSON blob from Redis under key "<flow>:<user_id>".
    If nothing is set, returns {}.
    """
    key = f"{flow}:{user_id}"
    data = redis_conn.get(key)
    if not data:
        return {}
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {}


def set_user_state(flow: str, user_id: str, new_state: dict):
    """
    Overwrite the JSON blob in Redis under key "<flow>:<user_id>".
    """
    key = f"{flow}:{user_id}"
    redis_conn.set(key, json.dumps(new_state))


def clear_user_state(flow: str, user_id: str):
    """
    Delete the Redis key "<flow>:<user_id>".
    """
    key = f"{flow}:{user_id}"
    redis_conn.delete(key)
