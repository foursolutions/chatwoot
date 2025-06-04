# helpers.py

import os
import redis
import json
import requests

# -------------------------------
#  ENV VARIABLES & INITIALIZATION
# -------------------------------
API_KEY_ENV            = os.getenv("1MSG_API_KEY")
BASE_URL_ENV           = os.getenv("1MSG_BASE_URL")
TEMPLATE_NAMESPACE_ENV = os.getenv("TEMPLATE_NAMESPACE")
REDIS_URL_ENV          = os.getenv("REDIS_URL")

print("=== ENV DEBUG ===")
print("1MSG_API_KEY        :", repr(API_KEY_ENV))
print("1MSG_BASE_URL       :", repr(BASE_URL_ENV))
print("TEMPLATE_NAMESPACE  :", repr(TEMPLATE_NAMESPACE_ENV))
print("REDIS_URL           :", repr(REDIS_URL_ENV))
print("=================\n")

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

# Initialize Redis (unchanged)
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# ====================================
#  Redis‐based State (unchanged)
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
#  Internal: POST to 1msg’s `/send` (text/interactive)
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
#  Internal: POST to 1msg’s `/sendMessage` (for templates)
# =====================================================
def _post_to_1msg_send_template(payload: dict) -> dict:
    # *** KEY CHANGE: use `/sendMessage` instead of `/sendTemplate` ***
    url = f"{BASE_URL}/sendMessage"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    print(">>> SENDING to /sendMessage:")
    print("    API_KEY        :", repr(API_KEY))
    print("    BASE_URL       :", repr(BASE_URL))
    print("    TEMPLATE_NS    :", repr(TEMPLATE_NAMESPACE))
    print("    FULL PAYLOAD   :", json.dumps(payload))
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print("[DEBUG] 1msg /sendMessage response:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


# =====================================================
#  Public: send_template_message (via `/sendMessage`)
# =====================================================
def send_template_message(to: str, template_name: str, template_params=None) -> dict:
    if template_params is None:
        template_params = []

    # Build the “params” array exactly as 1msg expects:
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
#  Public: send_interactive_message (via `/send`)
# ===============================================================
def send_interactive_message(payload: dict) -> dict:
    payload.setdefault("messaging_product", "whatsapp")
    return _post_to_1msg_send(payload)


# ================================================================
#  Public: send_text_message (via `/send`)
# ================================================================
def send_text_message(to: str, body: str) -> dict:
    payload = {
        "to":                to,
        "type":              "text",
        "text":              { "body": body },
        "messaging_product": "whatsapp"
    }
    return _post_to_1msg_send(payload)
