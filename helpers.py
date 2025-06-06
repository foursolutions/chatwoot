import os
import requests
import redis
import json

# ============
# Configuration
# ============
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
REDIS_URL      = os.getenv("REDIS_URL")

# Initialize Redis client (shared by all dynos)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


def get_user_state(prefix: str, user_number: str) -> dict:
    """
    Retrieve a user’s state (stored as JSON) from Redis.
    Returns {} if no state exists.
    """
    key = f"{prefix}:{user_number}"
    raw = r.get(key)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def set_user_state(prefix: str, user_number: str, state: dict, expire: int = 3600) -> None:
    """
    Save a user’s state (as JSON) in Redis with a TTL (default 1 hour).
    """
    key = f"{prefix}:{user_number}"
    serialized = json.dumps(state)
    r.set(key, serialized, ex=expire)


def clear_user_state(prefix: str, user_number: str) -> None:
    """
    Delete a user’s state from Redis.
    """
    key = f"{prefix}:{user_number}"
    r.delete(key)


def send_template_message(to: str, template_name: str, template_params: list) -> dict:
    """
    Send a template message via 360dialog V2 API.
    - `to`: recipient’s phone number as digits only (no “+”).
    - `template_name`: exact approved template name in 360dialog.
    - `template_params`: list of strings, one per placeholder in the template body.
    """
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "type": "template",
        "messaging_product": "whatsapp",
        "template": {
            "name": template_name,
            "language": {
                "code": "en_US",
                "policy": "deterministic"
            },
            "components": [
                {
                    "type": "BODY",
                    "parameters": [{"type": "text", "text": p} for p in template_params]
                }
            ]
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload)
        # Log full status and body for troubleshooting
        print(f"[DEBUG] send_template_message → status={resp.status_code} body={resp.text}")
        return resp.json()
    except Exception as e:
        print(f"[ERROR] send_template_message exception: {e}")
        return {"error": str(e)}


def send_interactive_message(payload: dict) -> dict:
    """
    Send any interactive (list or button) message.
    Expects a fully formed “payload” dict already including:
      - to, type="interactive", messaging_product="whatsapp", interactive:{…}
    """
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        print(f"[DEBUG] send_interactive_message → status={resp.status_code} body={resp.text}")
        return resp.json()
    except Exception as e:
        print(f"[ERROR] send_interactive_message exception: {e}")
        return {"error": str(e)}


def send_text_message(to: str, body: str) -> dict:
    """
    Send a plain text message.
    - `to`: recipient’s phone number as digits only (no “+”).
    - `body`: the text content.
    """
    url = "https://waba-v2.360dialog.io/messages"
    headers = {
        "D360-API-KEY": WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "type": "text",
        "messaging_product": "whatsapp",
        "text": {"body": body}
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        print(f"[DEBUG] send_text_message → status={resp.status_code} body={resp.text}")
        return resp.json()
    except Exception as e:
        print(f"[ERROR] send_text_message exception: {e}")
        return {"error": str(e)}
