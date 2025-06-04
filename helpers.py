# helpers.py

import os
import redis
import json
import requests

# ============================
#  Configuration & Constants
# ============================
#
# In Heroku Config Vars, you must have exactly:
#
#   1MSG_API_KEY       = <the API key from your 1msg dashboard>
#   1MSG_BASE_URL      = https://api.1msg.io/VAN388218473
#   TEMPLATE_NAMESPACE = 94d66366_9ec1_43a3_a84c_46039bd33ef5
#   REDIS_URL          = <your Redis connection URL>
#
# Remove any old 360dialog-only keys (WHATSAPP_TOKEN, D360-API_KEY) to avoid confusion.

API_KEY            = os.getenv("1MSG_API_KEY", "").strip()
BASE_URL           = os.getenv("1MSG_BASE_URL", "").rstrip("/")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE", "").strip()
REDIS_URL          = os.getenv("REDIS_URL", "").strip()

# Check that none of the required environment vars are missing
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

# Initialize Redis (for user state storage)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# ===================================
#  Redis-based State Functions
# ===================================
def get_user_state(prefix: str, user_id: str) -> dict:
    """
    Retrieve a JSON-encoded “flow state” for this user+prefix from Redis.
    If no state exists, returns {}.
    """
    key = f"{prefix}:{user_id}"
    raw = r.get(key)
    return json.loads(raw) if raw else {}


def set_user_state(prefix: str, user_id: str, state: dict):
    """
    Store a JSON-encoded “flow state” for this user+prefix in Redis, expires in 1 hour.
    """
    key = f"{prefix}:{user_id}"
    r.set(key, json.dumps(state), ex=3600)


def clear_user_state(prefix: str, user_id: str):
    """
    Delete any stored “flow state” for this user+prefix from Redis.
    """
    key = f"{prefix}:{user_id}"
    r.delete(key)


# =====================================================
#  Internal: call 1msg “/send” endpoint for text/interactive
# =====================================================
def _post_to_1msg_send(payload: dict) -> dict:
    """
    Internal helper: POST a 360dialog-style payload to 1msg’s /send endpoint.
    Use this for plain text and interactive messages.
    """
    url = f"{BASE_URL}/send"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    # Debug: print exactly what is being sent to /send
    print("[DEBUG] 1msg /send payload:", json.dumps(payload))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    # Debug: print 1msg’s raw response
    print("[DEBUG] 1msg /send response:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


# =====================================================
#  Internal: call 1msg “/sendTemplate” endpoint for templates
# =====================================================
def _post_to_1msg_send_template(payload: dict) -> dict:
    """
    Internal helper: POST a template-send payload to 1msg’s /sendTemplate endpoint.
    Follows 1msg’s schema: { token, namespace, template, language, params, phone }.
    """
    url = f"{BASE_URL}/sendTemplate"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    # Debug: print exactly what is being sent to /sendTemplate
    print("[DEBUG] 1msg /sendTemplate payload:", json.dumps(payload))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    # Debug: print 1msg’s raw response
    print("[DEBUG] 1msg /sendTemplate response:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


# =====================================================
#  Public: send_template_message (via 1msg → 360dialog)
# =====================================================
def send_template_message(to: str, template_name: str, template_params=None) -> dict:
    """
    Send a WhatsApp template message via 1msg’s /sendTemplate endpoint.
    
    - to:             recipient phone number (e.g. "6591234567")
    - template_name:  the short name of your 360dialog template (e.g. "main_menu_v2")
    - template_params: list of strings to fill {{1}}, {{2}}, etc. in the template body.
    
    Internally builds:
    {
      "token":     <API_KEY>,
      "namespace": <TEMPLATE_NAMESPACE>,
      "template":  <template_name>,
      "language": { "policy":"deterministic", "code":"en" },
      "params": [
        {
          "type": "body",
          "parameters": [ { "type":"text", "text": <param1> }, ... ]
        }
      ],
      "phone": <to>
    }
    """
    if template_params is None:
        template_params = []

    # Build the “params” array as 1msg expects:
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
        "language":  { "policy": "deterministic", "code": "en" },
        "params":    params_array,
        "phone":     to
    }

    return _post_to_1msg_send_template(payload)


# ===============================================================
#  Public: send_interactive_message (via 1msg → 360dialog)
# ===============================================================
def send_interactive_message(payload: dict) -> dict:
    """
    Send a “buttons” or “list” interactive message via 1msg’s /send endpoint.
    You must construct the payload in 360dialog format:
      {
        "to": "6591234567",
        "type": "interactive",
        "interactive": { ... },
        "messaging_product": "whatsapp"
      }
    1msg will forward it unchanged to 360dialog.
    """
    payload.setdefault("messaging_product", "whatsapp")
    return _post_to_1msg_send(payload)


# ================================================================
#  Public: send_text_message (via 1msg → 360dialog)
# ================================================================
def send_text_message(to: str, body: str) -> dict:
    """
    Send a simple text message (non-template) via 1msg’s /send endpoint.
    For example:
      {
        "to": "6591234567",
        "type": "text",
        "text": { "body": "Hello!" },
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
