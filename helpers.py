import os
import redis
import requests
import json
import logging

# Redis setup
redis_url = os.environ.get("REDIS_URL")
redis_client = redis.from_url(redis_url, decode_responses=True)

# Utilities for user state management
def get_user_state(key_prefix, chat_id):
    raw = redis_client.get(f"{key_prefix}:{chat_id}")
    return json.loads(raw) if raw else {}

def set_user_state(key_prefix, chat_id, value):
    redis_client.set(f"{key_prefix}:{chat_id}", json.dumps(value))

def clear_user_state(key_prefix, chat_id):
    redis_client.delete(f"{key_prefix}:{chat_id}")

# Normalizes text by stripping whitespace and lowercasing
def normalize_text(text):
    return text.strip().lower() if isinstance(text, str) else ""

# 1MSG Send functions
def send_text_message(to, text):
    payload = {
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    return _post_1msg(payload, tag="send_text_message")

def send_template_message(to, template_name, template_params=None):
    payload = {
        "to": to,
        "type": "template",
        "template": {
            "namespace": os.environ.get("TEMPLATE_NAMESPACE"),
            "name": template_name,
            "language": {"policy": "deterministic", "code": "en"},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": str(p)} for p in (template_params or [""])]
            }]
        }
    }
    return _post_1msg(payload, tag="send_template_message")

def send_interactive_message(to, payload):
    # Must include the interactive section within the payload already
    payload["to"] = to
    payload["type"] = "interactive"
    return _post_1msg(payload, tag="send_interactive_message")

def send_main_menu_template(chat_id):
    return send_template_message(chat_id, "main_menu_v2", [""])

# POST to 1MSG API
def _post_1msg(payload, tag=""):
    api_url = os.environ.get("ONE_MSG_API_URL")
    token = os.environ.get("ONE_MSG_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(f"{api_url}/messages", headers=headers, json=payload)
        logging.debug(f"[DEBUG] {tag} → 1MSG response: {resp.text}")
        return resp.json()
    except Exception as e:
        logging.error(f"[ERROR] {tag} → 1MSG exception: {e}")
        return {"error": str(e)}
