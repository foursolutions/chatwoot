# helpers.py

import os
import redis
import json
import requests

# -------------------------------
#  ENV VARIABLES & DEBUG OUTPUT
# -------------------------------
API_KEY_ENV            = os.getenv("1MSG_API_KEY")
BASE_URL_ENV           = os.getenv("1MSG_BASE_URL")
TEMPLATE_NAMESPACE_ENV = os.getenv("TEMPLATE_NAMESPACE")
REDIS_URL_ENV          = os.getenv("REDIS_URL")

# Print out the raw env vars so we can spot any typos or whitespace issues.
print("=== ENV DEBUG ===")
print("1MSG_API_KEY        :", repr(API_KEY_ENV))
print("1MSG_BASE_URL       :", repr(BASE_URL_ENV))
print("TEMPLATE_NAMESPACE  :", repr(TEMPLATE_NAMESPACE_ENV))
print("REDIS_URL           :", repr(REDIS_URL_ENV))
print("=================\n")

# Strip/clean them:
API_KEY            = API_KEY_ENV.strip()            if API_KEY_ENV            else ""
BASE_URL           = BASE_URL_ENV.rstrip("/")       if BASE_URL_ENV           else ""
TEMPLATE_NAMESPACE = TEMPLATE_NAMESPACE_ENV.strip() if TEMPLATE_NAMESPACE_ENV else ""
REDIS_URL          = REDIS_URL_ENV.strip()          if REDIS_URL_ENV          else ""

_missing = []
if not API_KEY:
    _missing.append("1MSG_API_KEY")
if not BASE_URL:
    _missing.append("1MSG_BASE_URL")
if not TEMPLATE_NAMESPACE:
    _missing.append("TEMPLATE_NAMESPACE")
if not REDIS_URL:
    _missing.append("REDIS_URL")

if _missing:
    raise RuntimeError(f"Missing required env var(s): {', '.join(_missing)}")

# Example values you should see:
# API_KEY            : 'TKNgRBqpmnDbRf9NzyO5uXNgKHobiDCe'
# BASE_URL           : 'https://api.1msg.io/VAN388218473'
# TEMPLATE_NAMESPACE : '94d66366_9ec1_43a3_a84c_46039bd33ef5'
# REDIS_URL          : 'redis://…'

# Initialize Redis client
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# ====================================
#  Redis-based State Functions (unchanged)
# ====================================
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
#  Internal: call 1msg’s `/send` for text/interactive
# =====================================================
def _post_to_1msg_send(payload: dict) -> dict:
    """
    Internal helper to POST a 360dialog-style payload to 1msg’s /send endpoint.
    Use this for text or interactive messages (buttons/lists).
    """
    url = f"{BASE_URL}/send"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    print("[DEBUG] 1msg /send payload:", json.dumps(payload))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print("[DEBUG] 1msg /send response:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


# =====================================================
#  Internal: call 1msg’s `/sendTemplate` for templates
# =====================================================
def _post_to_1msg_send_template(payload: dict) -> dict:
    """
    Internal helper to POST a 1msg-style template JSON to `/sendTemplate`.
    This is exactly what Dev Toolkit → Template uses under the hood.
    """
    url = f"{BASE_URL}/sendTemplate"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    print(">>> SENDING to /sendTemplate:")
    print("    API_KEY        :", repr(API_KEY))
    print("    BASE_URL       :", repr(BASE_URL))
    print("    TEMPLATE_NS    :", repr(TEMPLATE_NAMESPACE))
    print("    FULL PAYLOAD   :", json.dumps(payload))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print("[DEBUG] 1msg /sendTemplate response:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


# =====================================================
#  Public: send_template_message (POST to /sendTemplate)
# =====================================================
def send_template_message(to: str, template_name: str, template_params=None) -> dict:
    """
    Send a WhatsApp template via 1msg’s /sendTemplate endpoint.

    - to:            phone without “+” (e.g. "6591234567")
    - template_name: your 360dialog template name (e.g. "main_menu_v2")
    - template_params: list of strings to fill {{1}}, {{2}}, etc.

    Builds JSON like:
      {
        "token":     <API_KEY>,
        "namespace": <TEMPLATE_NAMESPACE>,
        "template":  <template_name>,
        "language":  { "policy":"deterministic", "code":"en" },
        "params": [
          {
            "type": "body",
            "parameters": [ { "type":"text", "text": <param> }, … ]
          }
        ],
        "phone":    "+<to>"
      }
    """
    if template_params is None:
        template_params = []

    params_array = []
    if template_params:
        params_array.append({
            "type": "body",
            "parameters": [
                {"type": "text", "text": param}
                for param in template_params
            ]
        })

    payload = {
        "token":     API_KEY,
        "namespace": TEMPLATE_NAMESPACE,
        "template":  template_name,
        "language":  {"policy": "deterministic", "code": "en"},
        "params":    params_array,
        "phone":     f"+{to}"   # MUST include “+”
    }

    return _post_to_1msg_send_template(payload)


# ===============================================================
#  Public: send_interactive_message (via /send)
# ===============================================================
def send_interactive_message(payload: dict) -> dict:
    """
    Send a 360dialog-style “interactive” (buttons/lists) payload via 1msg’s /send.
    Example payload:
      {
        "to":                "6591234567",
        "type":              "interactive",
        "interactive":       { … },
        "messaging_product": "whatsapp"
      }
    1msg will forward it unchanged to 360dialog.
    """
    payload.setdefault("messaging_product", "whatsapp")
    return _post_to_1msg_send(payload)


# ================================================================
#  Public: send_text_message (via /send)
# ================================================================
def send_text_message(to: str, body: str) -> dict:
    """
    Send a plain text message via 1msg’s /send (forwarded to 360dialog).
    Example:
      {
        "to":                "6591234567",
        "type":              "text",
        "text":              { "body": "Hello!" },
        "messaging_product": "whatsapp"
      }
    """
    payload = {
        "to":                to,
        "type":              "text",
        "text":              {"body": body},
        "messaging_product": "whatsapp"
    }
    return _post_to_1msg_send(payload)
