# helpers.py

import os
import redis
import requests

# ─── 1MSG CONFIG ────────────────────────────────────────────────────────────────
API_KEY_1MSG     = os.getenv("1MSG_API_KEY", "").strip()      # e.g. "TKNgrBqpmnbDhf9NzyO5uXNgKHoblDCe"
BASE_URL_1MSG    = os.getenv("1MSG_BASE_URL", "").rstrip("/") # e.g. "https://api.1msg.io/VAN388218473"
NAMESPACE_1MSG   = os.getenv("1MSG_NAMESPACE", "").strip()    # e.g. "94d66366_9ec1_43a3_a84c_46039bd33ef5"
LANG_CODE_1MSG   = os.getenv("1MSG_LANG_CODE", "en").strip()  # e.g. "en"
MAIN_MENU_TEMPLATE = os.getenv("MAIN_MENU_TEMPLATE", "main_menu_v2").strip()
PHONE_NUMBER_ID  = os.getenv("PHONE_NUMBER_ID", "").strip()   # e.g. "66681799847695"

# ─── REDIS SETUP FOR USER STATE ─────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def get_user_state(flow_prefix: str, user: str) -> dict:
    """
    Fetches a Redis hash at key "<flow_prefix>:<user>". Returns {} if none found.
    """
    raw = redis_client.hgetall(f"{flow_prefix}:{user}")
    return raw if raw else {}


def set_user_state(flow_prefix: str, user: str, state: dict):
    """
    Overwrites (or creates) the Redis hash at "<flow_prefix>:<user>".
    Expects `state` to be a simple dict of string→string.
    """
    redis_client.hset(f"{flow_prefix}:{user}", mapping=state)


def clear_user_state(flow_prefix: str, user: str):
    """
    Deletes the Redis key "<flow_prefix>:<user>" entirely.
    """
    redis_client.delete(f"{flow_prefix}:{user}")


# ─── 1) send_text_message: wrap 1MSG /sendMessage ───────────────────────────────
def send_text_message(message_payload: dict) -> dict:
    """
    Sends a plain‐text WhatsApp message via 1MSG's /sendMessage endpoint.

    Example payload:
      {
        "token": "TKNgrBqpmnbDhf9NzyO5uXNgKHoblDCe",
        "to": "6591234567",
        "type": "text",
        "messaging_product": "whatsapp",
        "text": { "body": "Hello world" }
      }
    """
    url = f"{BASE_URL_1MSG}/sendMessage"
    headers = {"Content-Type": "application/json"}

    # Insert the token at the top level of the JSON body
    body = {"token": API_KEY_1MSG}
    body.update(message_payload)

    resp = requests.post(url, json=body, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non-JSON response: {resp.text}"}


# ─── 2) send_template_message: wrap 1MSG /sendTemplate ──────────────────────────
def send_template_message(
    to: str,
    template_name: str,
    template_params: list[str] | None = None,
    language_code: str = LANG_CODE_1MSG,
    policy: str = "deterministic"
) -> dict:
    """
    Sends a pre‐approved WhatsApp Template via 1MSG's /sendTemplate endpoint.

      to              = phone number (digits only; e.g. "6591234567")
      template_name   = e.g. "main_menu_v2"
      template_params = e.g. ["there"]  if your template has one body parameter
    """
    if template_params is None:
        template_params = []

    # Build the "params" block
    params_body = {
        "type": "body",
        "parameters": [
            {"type": "text", "text": p}
            for p in template_params
        ]
    }

    url = f"{BASE_URL_1MSG}/sendTemplate"
    headers = {"Content-Type": "application/json"}

    payload = {
        "token": NAMESPACE_1MSG and API_KEY_1MSG or "",  # actually must always pass token first
        "namespace": NAMESPACE_1MSG,
        "template": template_name,
        "language": {"policy": policy, "code": language_code},
        "params": [params_body],
        "phone": to
    }

    # NOTE: we deliberately include "token" inside the JSON itself, per 1MSG’s requirement
    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non-JSON response: {resp.text}"}


# ─── 3) send_list_message: wrap 1MSG /sendList ──────────────────────────────────
def send_list_message(
    to: str,
    body: str,
    header: str,
    footer: str,
    action_title: str,
    sections: list[dict]
) -> dict:
    """
    Sends an interactive LIST via 1MSG's /sendList endpoint.

      to            = phone number (digits only)
      body          = the "body.text" field
      header        = header text (or "" if none)
      footer        = footer text (or "" if none)
      action_title  = value for "action.button"
      sections      = [
                        {
                          "title": "...",
                          "rows": [
                            {"id":"...","title":"...","description":"..."},
                            ...
                          ]
                        }
                      ]
    """
    url = f"{BASE_URL_1MSG}/sendList"
    headers = {"Content-Type": "application/json"}

    payload = {
        "token": API_KEY_1MSG,
        "body": body,
        "header": header,
        "footer": footer,
        "action": action_title,
        "sections": sections,
        "chatId": to
    }

    resp = requests.post(url, json=payload, headers=headers)
    try:
        return resp.json()
    except ValueError:
        return {"error": f"non-JSON response: {resp.text}"}
