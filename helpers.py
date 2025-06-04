# helpers.py

import os
import redis
import json
import requests

# ============================
#  Configuration & Constants
# ============================
# These must be set in your Heroku Config Vars:
#
#   1MSG_API_KEY       = (the API key from your 1msg dashboard)
#   1MSG_BASE_URL      = https://api.1msg.io/VAN388218473
#   TEMPLATE_NAMESPACE = 94d66366_9ec1_43a3_a84c_46039bd33ef5
#   REDIS_URL          = (your Redis connection URL)
#
# (You no longer need WHATSAPP_TOKEN or D360 API keys here.)

API_KEY            = os.getenv("1MSG_API_KEY")
BASE_URL           = os.getenv("1MSG_BASE_URL", "").rstrip("/")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE", "").strip()
REDIS_URL          = os.getenv("REDIS_URL")

if not API_KEY or not BASE_URL or not TEMPLATE_NAMESPACE or not REDIS_URL:
    raise RuntimeError(
        "Missing one of the required env vars: "
        "1MSG_API_KEY, 1MSG_BASE_URL, TEMPLATE_NAMESPACE, or REDIS_URL."
    )

# Initialize Redis client (unchanged)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# ===================================
#  Redis‐based State Functions (unchanged)
# ===================================
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
#  1msg “send”‐Endpoint Helper (replaces 360dialog V2)
# =====================================================
def _post_to_1msg(payload: dict) -> dict:
    """
    Internal helper: POST the given JSON payload to 1msg’s /send endpoint.
    Headers must include x-api-key: <your 1MSG_API_KEY>.
    """
    url = f"{BASE_URL}/send"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    # Uncomment for debugging if needed:
    # print("[1MSG SEND] HTTP", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


# ======================================================
#  send_template_message (via 1msg → 360dialog)
# ======================================================
def send_template_message(to: str, template_name: str, template_params=None):
    """
    Sends a WhatsApp template message through 1msg, forwarding to 360dialog.
    
    - to: recipient phone number (string, e.g. "6591234567")
    - template_name: the short name of your 360dialog template, e.g. "main_menu_v2"
    - template_params: list of strings to fill {{1}}, {{2}}, etc.
    """
    if template_params is None:
        template_params = []

    # Build body parameters exactly as 360dialog expects
    body_parameters = [{"type": "text", "text": param} for param in template_params]

    # Prepend namespace so 360dialog recognizes the template
    fully_qualified = f"{TEMPLATE_NAMESPACE}:{template_name}"

    payload = {
        "to": to,
        "type": "template",
        "template": {
            "name": fully_qualified,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": body_parameters
                }
            ]
        },
        "messaging_product": "whatsapp"
    }

    return _post_to_1msg(payload)


# ===============================================================
#  send_interactive_message (via 1msg → 360dialog)
# ===============================================================
def send_interactive_message(payload: dict):
    """
    Sends a “session‐based” interactive message (buttons or list) via 1msg,
    which forwards it to 360dialog unchanged. Ensure "messaging_product": "whatsapp" is set.
    """
    payload.setdefault("messaging_product", "whatsapp")
    return _post_to_1msg(payload)


# ================================================================
#  send_text_message (via 1msg → 360dialog)
# ================================================================
def send_text_message(to: str, body: str):
    """
    Sends a simple text message (non‐template) via 1msg,
    which forwards it to 360dialog. Include "messaging_product": "whatsapp".
    """
    payload = {
        "to": to,
        "type": "text",
        "text": {"body": body},
        "messaging_product": "whatsapp"
    }
    return _post_to_1msg(payload)
