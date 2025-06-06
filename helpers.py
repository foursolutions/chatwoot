# helpers.py
import os
import requests
import json
import redis
from typing import Dict, Optional

API_KEY      = os.getenv("1MSG_API_KEY")
BASE_URL     = os.getenv("1MSG_BASE_URL")
NAMESPACE    = os.getenv("1MSG_NAMESPACE")
LANG_CODE    = os.getenv("1MSG_LANG_CODE", "en")
PHONE_ID     = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

REDIS_URL    = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_user_state(prefix: str, phone: str) -> Dict:
    key = f"{prefix}:{phone}"
    raw = redis_client.get(key)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}

def set_user_state(prefix: str, phone: str, data: Dict) -> None:
    key = f"{prefix}:{phone}"
    redis_client.set(key, json.dumps(data))

def clear_user_state(prefix: str, phone: str) -> None:
    key = f"{prefix}:{phone}"
    redis_client.delete(key)

def send_text_message(
    to: str,
    body: str,
    footer: str = "",
    buttons: Optional[list] = None
) -> Dict:
    url = f"{BASE_URL}/sendButton"
    headers = {"Content-Type": "application/json"}

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
        "sections": sections_payload,
        "body": body,
        "footer": footer,
        "chatId": to
    }

    print("🔍 --> /sendButton payload:", json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"🔍 /sendButton HTTP status: {resp.status_code}, response JSON: {resp.text}")
    resp.raise_for_status()
    return resp.json()

def send_template_message(
    to: str,
    template_name: str,
    template_params: Optional[list] = None
) -> Dict:
    """
    Sends a pre‐approved WhatsApp template via 1msg's /sendTemplate.
    - `to`: must be in the format "65xxxxxxxx@c.us".
    - `template_name`: e.g. "main_menu_v2".
    - `template_params`: a list of strings for placeholder substitution.
    """
    url = f"{BASE_URL}/sendTemplate"
    headers = {"Content-Type": "application/json"}

    if template_params is None:
        template_params = []

    # Convert each string into the object {type:"TEXT", text: "..."}
    params_payload = []
    for text in template_params:
        params_payload.append({
            "type": "TEXT",
            "text": text
        })

    payload = {
        "token": API_KEY,
        "namespace": NAMESPACE,
        "template": template_name,
        "language": {"policy": "deterministic", "code": LANG_CODE},
        "params": params_payload,
        "chatId": to
    }

    print("🔍 --> /sendTemplate payload:", json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"🔍 /sendTemplate HTTP status: {resp.status_code}, response JSON: {resp.text}")
    resp.raise_for_status()
    return resp.json()

def send_list_message(
    to: str,
    body: str = "",
    header: str = "",
    footer: str = "",
    action: str = "",
    sections: Optional[list] = None
) -> Dict:
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

    print("🔍 --> /sendList payload:", json.dumps(payload, ensure_ascii=False))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"🔍 /sendList HTTP status: {resp.status_code}, response JSON: {resp.text}")
    resp.raise_for_status()
    return resp.json()
