# helpers.py

import os
import requests
import json
import redis
from typing import Dict, Optional

# ─── 1. Load ENV VARIABLES ────────────────────────────────────────────────────────
API_KEY      = os.getenv("1MSG_API_KEY")        # e.g. "TKNgrBqpmnDbhF9NzyO5uXNgKHoblDCe"
BASE_URL     = os.getenv("1MSG_BASE_URL")       # e.g. "https://api.1msg.io/VAN388218473"
NAMESPACE    = os.getenv("1MSG_NAMESPACE")      # e.g. "94d66366_9ec1_43a3_a84c_46039bd33ef5"
LANG_CODE    = os.getenv("1MSG_LANG_CODE", "en")# e.g. "en"
PHONE_ID     = os.getenv("PHONE_NUMBER_ID")     # (optional, for media endpoints if needed)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")        # used for /verify webhook

REDIS_URL    = os.getenv("REDIS_URL")           # your Redis connection string
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


# ─── 2. STATE MANAGEMENT ──────────────────────────────────────────────────────────
def get_user_state(prefix: str, phone: str) -> Dict:
    """
    Fetch a JSON‐encoded state dict from Redis.
    If no data exists or JSON is invalid, return {}.
    """
    key = f"{prefix}:{phone}"
    raw = redis_client.get(key)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def set_user_state(prefix: str, phone: str, data: Dict) -> None:
    """
    Save a JSON‐encoded state under "<prefix>:<phone>".
    Overwrites any previous state.
    """
    key = f"{prefix}:{phone}"
    redis_client.set(key, json.dumps(data))


def clear_user_state(prefix: str, phone: str) -> None:
    """
    Delete the Redis key "<prefix>:<phone>" entirely.
    """
    key = f"{prefix}:{phone}"
    redis_client.delete(key)


# ─── 3. SEND PLAIN TEXT or BUTTONS ────────────────────────────────────────────────
def send_text_message(
    to: str,
    body: str,
    footer: str = "",
    buttons: Optional[list] = None
) -> Dict:
    """
    Send either plain text or a set of reply‐buttons via 1msg's /sendButton endpoint.
    - `to`: must be "65xxxxxxxx@c.us"
    - `body`: the main message text
    - `footer`: optional footer text under the body
    - `buttons`: a list of dicts, each {"id": "<unique_id>", "title": "<button text>"}
    """
    url = f"{BASE_URL}/sendButton"
    headers = {"Content-Type": "application/json"}

    # Build the "sections" array for buttons if provided
    sections_payload = []
    if buttons:
        for btn in buttons:
            sections_payload.append({
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"]
                }
            })

    payload = {
        "token": API_KEY,
        "sections": sections_payload,   # empty list => no buttons
        "body": body,
        "footer": footer,
        "chatId": to
    }

    # Debug print
    print("🔍 --> /sendButton payload:", json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"🔍 /sendButton HTTP status: {resp.status_code}, response JSON: {resp.text}")
    resp.raise_for_status()
    return resp.json()


# ─── 4. SEND A TEMPLATE ──────────────────────────────────────────────────────────
def send_template_message(
    to: str,
    template_name: str,
    template_params: Optional[list] = None
) -> Dict:
    """
    Send a pre-approved WhatsApp template via 1msg's /sendTemplate endpoint.
    - `to`: must be "65xxxxxxxx@c.us"
    - `template_name`: e.g., "main_menu_v2"
    - `template_params`: list of strings to fill {{1}}, {{2}}, etc.
    """
    url = f"{BASE_URL}/sendTemplate"
    headers = {"Content-Type": "application/json"}

    if template_params is None:
        template_params = []

    # Convert each simple string into the expected {type:"TEXT", string:"..."} object
    params_payload = []
    for txt in template_params:
        params_payload.append({
            "type": "TEXT",
            "string": txt
        })

    payload = {
        "token": API_KEY,
        "namespace": NAMESPACE,
        "template": template_name,
        "language": {"policy": "deterministic", "code": LANG_CODE},
        "params": params_payload,
        "chatId": to
    }

    # Debug prints
    print("🔍 --> /sendTemplate payload:", json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"🔍 /sendTemplate HTTP status: {resp.status_code}, response JSON: {resp.text}")
    resp.raise_for_status()
    return resp.json()


# ─── 5. SEND A LIST ───────────────────────────────────────────────────────────────
def send_list_message(
    to: str,
    body: str = "",
    header: str = "",
    footer: str = "",
    action: str = "",
    sections: Optional[list] = None
) -> Dict:
    """
    Send an interactive list via 1msg's /sendList endpoint.
    - `to`: must be "65xxxxxxxx@c.us"
    - `body`: instruction or message text
    - `header`: optional header title
    - `footer`: optional footer text
    - `action`: the label on the select‐button at the bottom
    - `sections`: list of section dicts, each having:
         {
            "title": "<section header>",
            "rows": [
               {"id":"<row_id>", "title":"<row label>", "description":"<desc>"},
               ...
            ]
         }
    """
    url = f"{BASE_URL}/sendList"
    headers = {"Content-Type": "application/json"}

    if sections is None:
        sections = []

    payload = {
        "token": API_KEY,
        "body": body,
        "header": header,
        "footer": footer,
        "action": action,
        "sections": sections,
        "chatId": to
    }

    # Debug prints
    print("🔍 --> /sendList payload:", json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"🔍 /sendList HTTP status: {resp.status_code}, response JSON: {resp.text}")
    resp.raise_for_status()
    return resp.json()
