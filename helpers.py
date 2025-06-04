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
#   1MSG_API_KEY       = <your 1msg API key>               (e.g. TKNgR...HoMlDCe)
#   1MSG_BASE_URL      = https://api.1msg.io/VAN388218473   (no trailing slash)
#   TEMPLATE_NAMESPACE = 94d66366_9ec1_43a3_a84c_46039bd33ef5
#   REDIS_URL          = <your redis:// URL>
#
# Remove any old 360dialog‐only keys (WHATSAPP_TOKEN, D360‐API‐KEY) to avoid confusion.

API_KEY            = os.getenv("1MSG_API_KEY", "").strip()
BASE_URL           = os.getenv("1MSG_BASE_URL", "").rstrip("/")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE", "").strip()
REDIS_URL          = os.getenv("REDIS_URL", "").strip()

# Basic validations
missing = []
if not API_KEY:
    missing.append("1MSG_API_KEY")
if not BASE_URL:
    missing.append("1MSG_BASE_URL")
if not TEMPLATE_NAMESPACE:
    missing.append("TEMPLATE_NAMESPACE")
if not REDIS_URL:
    missing.append("REDIS_URL")
if missing:
    raise RuntimeError(f"Missing required env var(s): {', '.join(missing)}")

# Example:
#   BASE_URL might be "https://api.1msg.io/VAN388218473"
#   So the template‐send URL will be "https://api.1msg.io/VAN388218473/sendTemplate"
#   and the regular send URL will be    "https://api.1msg.io/VAN388218473/send"


# =====================================================
#  Redis‐based State Functions (unchanged)
# =====================================================
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

def get_user_state(prefix: str, user_id: str) -> dict:
    """
    Retrieve a JSON‐encoded state object for this user+flow from Redis.
    Returns an empty dict if no state is found.
    """
    key = f"{prefix}:{user_id}"
    raw = r.get(key)
    return json.loads(raw) if raw else {}


def set_user_state(prefix: str, user_id: str, state: dict):
    """
    Store a JSON‐encoded state object for this user+flow into Redis with 1h TTL.
    """
    key = f"{prefix}:{user_id}"
    r.set(key, json.dumps(state), ex=3600)


def clear_user_state(prefix: str, user_id: str):
    """
    Delete this user+flow key from Redis (clearing their session state).
    """
    key = f"{prefix}:{user_id}"
    r.delete(key)


# =====================================================
#  Internal: call 1msg “/send” endpoint for text/interactive
# =====================================================
def _post_to_1msg_send(payload: dict) -> dict:
    """
    Internal helper to post a 360dialog‐style payload to 1msg’s /send endpoint.
    E.g. for text messages or interactive messages.
    """
    url = f"{BASE_URL}/send"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    # If you need to debug, uncomment:
    # print("[1MSG /send] HTTP", resp.status_code, "→", resp.text)
    resp.raise_for_status()
    return resp.json()


# =====================================================
#  Internal: call 1msg “/sendTemplate” endpoint for templates
# =====================================================
def _post_to_1msg_send_template(payload: dict) -> dict:
    """
    Internal helper to post a template‐send payload to 1msg’s /sendTemplate endpoint.
    Follows 1msg’s own schema: { token, namespace, template, language, params, phone }.
    """
    url = f"{BASE_URL}/sendTemplate"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    # If you need to debug, uncomment:
    # print("[1MSG /sendTemplate] HTTP", resp.status_code, "→", resp.text)
    resp.raise_for_status()
    return resp.json()


# =====================================================
#  Public: send_template_message (via 1msg → 360dialog)
# =====================================================
def send_template_message(to: str, template_name: str, template_params=None) -> dict:
    """
    Send a WhatsApp template via 1msg’s /sendTemplate endpoint.

    - to: the phone number in international format without “+” (e.g. "6591234567")
    - template_name: short name in your 360dialog template list, e.g. "main_menu_v2"
      (without the namespace—this function will prepend TEMPLATE_NAMESPACE for you)
    - template_params: list of strings, each one filling {{1}}, {{2}}, etc. in the template body.

    This function builds the JSON payload exactly as 1msg expects, e.g.:

      {
        "token":      "<API_KEY>",
        "namespace":  "<TEMPLATE_NAMESPACE>",
        "template":   "main_menu_v2",
        "language":   { "policy": "deterministic", "code": "en" },
        "params": [
          { "type": "body", "parameters": [ { "type": "text", "text": "there" } ] }
        ],
        "phone":      "6591234567"
      }
    """
    if template_params is None:
        template_params = []

    # Build the “body” params array
    # For each string in template_params, we wrap it in:
    #    { "type": "body", "parameters": [ { "type": "text", "text": param } ] }
    #
    # Note: 1msg expects a single “params” array (not separate “header”/“button” components).
    # At the moment, our templates only use body‐params.
    params_array = []
    if len(template_params) > 0:
        # 1msg’s schema: one object: { type:"body", parameters:[ { type:"text", text:param } ] }
        params_array.append({
            "type": "body",
            "parameters": [
                { "type": "text", "text": param }
                for param in template_params
            ]
        })

    payload = {
        "token":     API_KEY,
        "namespace": TEMPLATE_NAMESPACE,
        "template":  template_name,
        "language": {
            "policy": "deterministic",
            "code":   "en"
        },
        "params": params_array,
        "phone": to
    }

    return _post_to_1msg_send_template(payload)


# =====================================================
#  Public: send_interactive_message (via 1msg → 360dialog)
# =====================================================
def send_interactive_message(payload: dict) -> dict:
    """
    Send a “buttons” or “list” interactive message via 1msg’s /send.
    You must construct the payload in 360dialog format (as if you were sending directly to 360dialog).

    Example (buttons):
      {
        "to":      "6591234567",
        "type":    "interactive",
        "interactive": {
           "type": "button",
           "body":     { "text": "Select an option:" },
           "action":   { "buttons":[ { "type":"reply", "reply":{ "id":"opt1","title":"Option 1" } }, … ] }
        },
        "messaging_product": "whatsapp"
      }

    1msg will forward it to 360dialog unchanged (you just need to set messaging_product).
    """
    payload.setdefault("messaging_product", "whatsapp")
    return _post_to_1msg_send(payload)


# =====================================================
#  Public: send_text_message (via 1msg → 360dialog)
# =====================================================
def send_text_message(to: str, body: str) -> dict:
    """
    Send a plain “text” message via 1msg’s /send endpoint (forwarded to 360dialog).
    Example:
      {
        "to":      "6591234567",
        "type":    "text",
        "text":    { "body": "Hello there!" },
        "messaging_product":"whatsapp"
      }
    """
    payload = {
        "to":                to,
        "type":              "text",
        "text":              { "body": body },
        "messaging_product": "whatsapp"
    }
    return _post_to_1msg_send(payload)
