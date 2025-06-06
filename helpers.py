# helpers.py
import os
import requests
import json
import redis
from typing import Dict, Optional

# ─── 1. Load ENV VARIABLES ────────────────────────────────────────────────────────
API_KEY        = os.getenv("1MSG_API_KEY")        # e.g. "TKNgrBqpmnDbhF9NzyO5uXNgKHoblDCe"
BASE_URL       = os.getenv("1MSG_BASE_URL")       # e.g. "https://api.1msg.io/VAN388218473"
NAMESPACE      = os.getenv("1MSG_NAMESPACE")      # e.g. "94d66366_9ec1_43a3_a84c_46039bd33ef5"
LANG_CODE      = os.getenv("1MSG_LANG_CODE", "en")# e.g. "en"
PHONE_ID       = os.getenv("PHONE_NUMBER_ID")     # (You may or may not need this for media or other calls)
VERIFY_TOKEN   = os.getenv("VERIFY_TOKEN")        # Used for /verify endpoint, not POSTing to 1msg

REDIS_URL      = os.getenv("REDIS_URL")           # your Redis connection string
redis_client   = redis.from_url(REDIS_URL, decode_responses=True)


# ─── 2. STATE MANAGEMENT: get_user_state / set_user_state / clear_user_state ─────
#
# We store per‐user state (a simple JSON blob) under a Redis key like "<prefix>:<phone>"
# Example prefix might be "CAR_FUM" or "MAIN_MENU" or anything you choose.  
# The flow code typically does:
#   user_state = get_user_state("CAR_FUM", phone_number)
#   set_user_state("CAR_FUM", phone_number, { ... updated dict ... })
#   clear_user_state("CAR_FUM", phone_number)       # resets that state to an empty dict
#

def get_user_state(prefix: str, phone: str) -> Dict:
    """
    Fetches a JSON‐encoded state from Redis. If missing, returns {}.
    """
    key = f"{prefix}:{phone}"
    raw = redis_client.get(key)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}

def set_user_state(prefix: str, phone: str, data: Dict) -> None:
    """
    Saves a JSON‐encoded state under "<prefix>:<phone>".
    """
    key = f"{prefix}:{phone}"
    redis_client.set(key, json.dumps(data))

def clear_user_state(prefix: str, phone: str) -> None:
    """
    Deletes the key "<prefix>:<phone>" entirely.
    """
    key = f"{prefix}:{phone}"
    redis_client.delete(key)


# ─── 3. SENDING PLAIN TEXT or BUTTONS: send_text_message ────────────────────────
#
# 1msg’s “/sendButton” expects JSON of the form (see your images):
#
#   {
#     "token":  "<YOUR_API_KEY>",
#     "sections": [
#       {
#         "type": "reply",
#         "reply": {
#            "id": "<some_id>",
#            "title": "<button text>"
#         }
#       },
#       ...
#     ],
#     "body": "<body_text>",
#     "footer": "<footer_text>",
#     "chatId": "<user_phone@c.us>"
#   }
#
# Note: you can send zero buttons (just a “body” + “chatId”) if you want plain text.
# The helper can accept a dict (payload already built) or build it here. 
#

def send_text_message(to: str, body: str, footer: str = "", buttons: Optional[list] = None) -> Dict:
    """
    Sends either a plain text or a set of "reply" buttons.
    - `to`: must be in the format "65xxxxxxxx@c.us" (no spaces).
    - `body`: the main text
    - `buttons`: a list of dicts, each dict is {"id": "...", "title": "..."}.
    - `footer`: optional footer text under the body
    """
    url = f"{BASE_URL}/sendButton"
    headers = {"Content-Type": "application/json"}

    # Build the "sections" array if buttons were passed; otherwise, send only body/footer
    sections_payload = []
    if buttons:
        # 1msg expects each button wrapped inside a "reply" object, plus a "type":"reply" at top
        for btn in buttons:
            # Each `btn` must be {"id": "<unique_id>", "title": "<button label>"}
            sections_payload.append({
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"]
                }
            })

    payload = {
        "token": API_KEY,
        "sections": sections_payload,   # can be empty list => no buttons
        "body": body,
        "footer": footer,
        "chatId": to
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ─── 4. SENDING A TEMPLATE: send_template_message ───────────────────────────────
#
# 1msg’s `/sendTemplate` expects JSON:
#
#   {
#     "token": "<YOUR_API_KEY>",
#     "namespace": "<YOUR_NAMESPACE>",
#     "template": "<TEMPLATE_NAME>",
#     "language": {
#         "policy": "deterministic",
#         "code": "<LANG_CODE>"
#     },
#     "params": [ /* array of strings to fill placeholders */ ],
#     "chatId": "<user_phone@c.us>"
#   }
#

def send_template_message(to: str, template_name: str, template_params: Optional[list] = None) -> Dict:
    """
    Sends a pre‐approved WhatsApp template.
    - `to`: must be in the format "65xxxxxxxx@c.us".
    - `template_name`: e.g. "main_menu_v2"
    - `template_params`: a list of strings (or numbers) for placeholder substitution.
    """
    url = f"{BASE_URL}/sendTemplate"
    headers = {"Content-Type": "application/json"}

    if template_params is None:
        template_params = []

    payload = {
        "token": API_KEY,
        "namespace": NAMESPACE,
        "template": template_name,
        "language": {
            "policy": "deterministic",
            "code": LANG_CODE
        },
        "params": template_params,    # e.g. ["John"] if your template has {{1}}
        "chatId": to                  # e.g. "6587788080@c.us"
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ─── 5. SENDING A LIST: send_list_message ───────────────────────────────────────
#
# 1msg’s `/sendList` expects JSON:
#
#   {
#     "token": "<YOUR_API_KEY>",
#     "body":    "<body_text>",
#     "header":  "<header_text>",
#     "footer":  "<footer_text>",
#     "action":  "<action_button_label>",
#     "sections": [
#        {
#          "title": "<section_title>",
#          "rows": [
#             {
#               "id": "<row_id>",
#               "title": "<row_label>",
#               "description": "<row_desc>"
#             },
#             ...
#           ]
#        },
#        ...
#     ],
#     "chatId": "<user_phone@c.us>"
#   }
#

def send_list_message(
    to: str,
    body: str = "",
    header: str = "",
    footer: str = "",
    action: str = "",
    sections: Optional[list] = None
) -> Dict:
    """
    Sends an interactive list (multi‐section).
    - `to`: "65xxxxxxxx@c.us"
    - `body`: main instruction (e.g. "Please choose an option:")
    - `header`: optional header
    - `footer`: optional footer
    - `action`: the “Select an option” button text at bottom
    - `sections`: a Python list of section‐dicts, where each section is:
         {
            "title": "<section header>",
            "rows": [
               {"id": "<unique_id>", "title": "<menu text>", "description": "<desc>"},
               ...
            ]
         }
    """
    url = f"{BASE_URL}/sendList"
    headers = {"Content-Type": "application/json"}

    if sections is None:
        sections = []

    payload = {
        "token": API_KEY,
        "body": body,
        "header": header,
        "footer": footer,
        "action": action,
        "sections": sections,   # See above format
        "chatId": to
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()
