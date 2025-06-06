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
PHONE_ID     = os.getenv("PHONE_NUMBER_ID")     # (may be unused here)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")        # for your /verify endpoint

REDIS_URL    = os.getenv("REDIS_URL")           # your Redis connection string
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


# ─── 2. STATE MANAGEMENT: get_user_state / set_user_state / clear_user_state ─────
def get_user_state(prefix: str, phone: str) -> Dict:
    """
    Fetches a JSON‐encoded state from Redis. If missing or invalid, returns {}.
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
    Saves a JSON‐encoded state under "<prefix>:<phone>".
    """
    key = f"{prefix}:{phone}"
    redis_client.set(key, json.dumps(data))

def clear_user_state(prefix: str, phone: str) -> None:
    """
    Deletes the key "<prefix>:<phone>" entirely.
    """
    key = f"{prefix}:{phone}"
    redis_client.delete(key)


# ─── 3. SENDING PLAIN TEXT or BUTTONS: send_text_message ────────────────────────
def send_text_message(
    to: str,
    body: str,
    footer: str = "",
    buttons: Optional[list] = None
) -> Dict:
    """
    Sends either a plain text or a set of "reply" buttons via 1msg's /sendButton.
    - `to`: must be in the format "65xxxxxxxx@c.us".
    - `body`: the main message text.
    - `footer`: optional footer text beneath the body.
    - `buttons`: a list of dicts, each dict is {"id": "<unique_id>", "title": "<button text>"}.
    """
    url = f"{BASE_URL}/sendButton"
    headers = {"Content-Type": "application/json"}

    # Build the "sections" array if buttons were passed; otherwise, keep it empty
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
        "sections": sections_payload,   # can be empty list => no buttons
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


# ─── 4. SENDING A TEMPLATE: send_template_message ───────────────────────────────
def send_template_message(
    to: str,
    template_name: str,
    template_params: Optional[list] = None
) -> Dict:
    """
    Sends a pre‐approved WhatsApp template via 1msg's /sendTemplate.
    - `to`: must be in the format "65xxxxxxxx@c.us".
    - `template_name`: e.g. "main_menu_v2".
    - `template_params`: a list of strings (or numbers) for placeholder substitution.
    """
    url = f"{BASE_URL}/sendTemplate"
    headers = {"Content-Type": "application/json"}

    if template_params is None:
        template_params = []

    payload = {
        "token": API_KEY,
        "namespace": NAMESPACE,
        "template": template_name,
        "language": {"policy": "deterministic", "code": LANG_CODE},
        "params": template_params,
        "chatId": to
    }

    # Debug prints
    print("🔍 --> /sendTemplate payload:", json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"🔍 /sendTemplate HTTP status: {resp.status_code}, response JSON: {resp.text}")
    resp.raise_for_status()
    return resp.json()


# ─── 5. SENDING A LIST: send_list_message ───────────────────────────────────────
def send_list_message(
    to: str,
    body: str = "",
    header: str = "",
    footer: str = "",
    action: str = "",
    sections: Optional[list] = None
) -> Dict:
    """
    Sends an interactive list via 1msg's /sendList.
    - `to`: "65xxxxxxxx@c.us"
    - `body`: main instruction text (e.g. "Please choose an option:")
    - `header`: optional header title
    - `footer`: optional footer text
    - `action`: the text on the "Select an option" button
    - `sections`: a Python list of section‐dicts, each section is:
         {
            "title": "<section header>",
            "rows": [
               {"id": "<row_id>", "title": "<row_label>", "description": "<desc>"},
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
