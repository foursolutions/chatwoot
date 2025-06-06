# helpers.py (no changes needed)
import os
import requests
import redis
import json

ONE_MSG_API_URL = os.getenv("ONE_MSG_API_URL")  # e.g. "https://api.1msg.io/VAN388218473"
ONE_MSG_TOKEN   = os.getenv("ONE_MSG_TOKEN")    # e.g. "TKNgrBqpmnbDhF9NzyO5uXNgKHoblDCe"
REDIS_URL       = os.getenv("REDIS_URL")
TEMPLATE_NAMESPACE = os.getenv("TEMPLATE_NAMESPACE")

if not ONE_MSG_API_URL or not ONE_MSG_TOKEN:
    raise EnvironmentError(
        "ONE_MSG_API_URL and ONE_MSG_TOKEN must be set in your environment."
    )

ONE_MSG_API_URL = ONE_MSG_API_URL.rstrip("/")

r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

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

def send_text_message(to: str, body: str):
    url = f"{ONE_MSG_API_URL}/sendMessage"
    payload = {
        "token": ONE_MSG_TOKEN,
        "body": body,
        "phone": to
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        print(f"[ERROR] send_text_message to={to} payload={json.dumps(payload)} error={e}")
        result = {"error": str(e)}
    print(f"[DEBUG] send_text_message → 1MSG response: {result}")
    return result

def send_interactive_message(payload: dict):
    """
    (Unchanged) Transforms your “interactive” payload into either /sendList or /sendButton
    calls on 1MSG.
    """
    try:
        interactive = payload.get("interactive", {})
        i_type = interactive.get("type")
        to = payload.get("to")
        if not to or not i_type:
            raise ValueError("Missing 'to' or 'interactive.type' in payload")

        # ── LIST CASE ──
        if i_type == "list":
            header_text = interactive.get("header", {}).get("text", "")
            body_text   = interactive.get("body", {}).get("text", "")
            footer_text = interactive.get("footer", {}).get("text", "")
            action_obj  = interactive.get("action", {})
            action_button = action_obj.get("button", "")

            # Build 1MSG‐style sections array
            sections_1msg = []
            for sec in action_obj.get("sections", []):
                title = sec.get("title", "")
                rows  = sec.get("rows", [])
                sections_1msg.append({
                    "title": title,
                    "rows": rows
                })

            payload_1msg = {
                "token": ONE_MSG_TOKEN,
                "header": header_text,
                "body": body_text,
                "footer": footer_text,
                "action": action_button,
                "sections": sections_1msg,
                "phone": to
            }
            url = f"{ONE_MSG_API_URL}/sendList"
            resp = requests.post(url, json=payload_1msg, timeout=10)
            resp.raise_for_status()
            result = resp.json()

        # ── BUTTON CASE ──
        elif i_type == "button":
            body_text   = interactive.get("body", {}).get("text", "")
            footer_text = payload.get("footer", "") or ""
            buttons = interactive.get("action", {}).get("buttons", [])

            sections_1msg = []
            for btn in buttons:
                reply_obj = btn.get("reply", {})
                btn_id    = reply_obj.get("id")
                btn_title = reply_obj.get("title")
                sections_1msg.append({
                    "type": "reply",
                    "reply": {
                        "id": btn_id,
                        "title": btn_title
                    }
                })

            payload_1msg = {
                "token": ONE_MSG_TOKEN,
                "sections": sections_1msg,
                "body": body_text,
                "footer": footer_text,
                "phone": to
            }
            url = f"{ONE_MSG_API_URL}/sendButton"
            resp = requests.post(url, json=payload_1msg, timeout=10)
            resp.raise_for_status()
            result = resp.json()

        else:
            raise ValueError(f"Unsupported interactive.type='{i_type}'")

    except Exception as e:
        print(f"[ERROR] send_interactive_message failed. incoming_payload={json.dumps(payload)} error={e}")
        result = {"error": str(e)}

    print(f"[DEBUG] send_interactive_message → 1MSG response: {result}")
    return result

def send_template_message(to: str, template_name: str, template_params=None):
    """
    (Unchanged) Builds 1MSG /sendTemplate payload from your template name + params.
    """
    if template_params is None:
        template_params = []

    body_parameters = []
    for param in template_params:
        body_parameters.append({
            "type": "text",
            "text": param
        })
    params_array = [
        {
            "type": "body",
            "parameters": body_parameters
        }
    ]

    payload_1msg = {
        "token": ONE_MSG_TOKEN,
        "namespace": TEMPLATE_NAMESPACE,
        "template": template_name,
        "language": {
            "policy": "deterministic",
            "code": "en"
        },
        "params": params_array,
        "phone": to
    }

    url = f"{ONE_MSG_API_URL}/sendTemplate"
    try:
        resp = requests.post(url, json=payload_1msg, timeout=10)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        print(f"[ERROR] send_template_message to={to}, template={template_name}, payload={json.dumps(payload_1msg)} error={e}")
        result = {"error": str(e)}

    print(f"[DEBUG] send_template_message → 1MSG response: {result}")
    return result
