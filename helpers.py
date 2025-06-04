# helpers.py

import os
import redis
import json
import requests

# ------------------
#  ENV DEBUGGING
# ------------------
# As soon as this file is imported, print out the three critical env vars.
# You should NOT see any extra whitespace, “None,” or empty strings here.
API_KEY_ENV           = os.getenv("1MSG_API_KEY")
BASE_URL_ENV          = os.getenv("1MSG_BASE_URL")
TEMPLATE_NAMESPACE_ENV = os.getenv("TEMPLATE_NAMESPACE")
REDIS_URL_ENV         = os.getenv("REDIS_URL")

print("=== ENV DEBUG ===")
print("1MSG_API_KEY        :", repr(API_KEY_ENV))
print("1MSG_BASE_URL       :", repr(BASE_URL_ENV))
print("TEMPLATE_NAMESPACE  :", repr(TEMPLATE_NAMESPACE_ENV))
print("REDIS_URL           :", repr(REDIS_URL_ENV))
print("=================\n")

# ============================
#  Configuration & Constants
# ============================
API_KEY            = API_KEY_ENV.strip() if API_KEY_ENV else ""
BASE_URL           = BASE_URL_ENV.rstrip("/") if BASE_URL_ENV else ""
TEMPLATE_NAMESPACE = TEMPLATE_NAMESPACE_ENV.strip() if TEMPLATE_NAMESPACE_ENV else ""
REDIS_URL          = REDIS_URL_ENV.strip() if REDIS_URL_ENV else ""

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

# Initialize Redis (unchanged)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# =====================================================
#  Redis-based State Functions (unchanged)
# =====================================================
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
#  Internal: call 1msg “/send” endpoint for text/interactive
# =====================================================
def _post_to_1msg_send(payload: dict) -> dict:
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
#  Internal: call 1msg “/sendTemplate” endpoint for templates
# =====================================================
def _post_to_1msg_send_template(payload: dict) -> dict:
    url = f"{BASE_URL}/sendTemplate"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    # Print the three critical values again right before we send:
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
#  Public: send_template_message (via 1msg → 360dialog)
# =====================================================
def send_template_message(to: str, template_name: str, template_params=None) -> dict:
    if template_params is None:
        template_params = []

    params_array = []
    if template_params:
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
        "language":  { "policy": "deterministic", "code": "en" },
        "params":    params_array,
        "phone":     f"+{to}"     # MUST prefix with “+”
    }

    return _post_to_1msg_send_template(payload)


# ===============================================================
#  Public: send_interactive_message (via 1msg → 360dialog)
# ===============================================================
def send_interactive_message(payload: dict) -> dict:
    payload.setdefault("messaging_product", "whatsapp")
    return _post_to_1msg_send(payload)


# ================================================================
#  Public: send_text_message (via 1msg → 360dialog)
# ================================================================
def send_text_message(to: str, body: str) -> dict:
    payload = {
        "to":                to,
        "type":              "text",
        "text":              { "body": body },
        "messaging_product": "whatsapp"
    }
    return _post_to_1msg_send(payload)
