import requests
import os

API_URL = os.environ.get("WHATSAPP_API_URL")
TOKEN = os.environ.get("WHATSAPP_API_TOKEN")

def send_text_message(chat_id, text):
    payload = {
        "chatId": chat_id,
        "body": text
    }
    return send_request("/message", payload)

def send_template_message(chat_id, template_name):
    payload = {
        "chatId": chat_id,
        "template": template_name
    }
    return send_request("/sendTemplate", payload)

def send_main_menu_template(chat_id):
    return send_template_message(chat_id, "main_menu_v2")

def send_interactive_message(chat_id, content):
    payload = {
        "chatId": chat_id,
        "interactive": content
    }
    return send_request("/interactive", payload)

def send_list_message(chat_id, header, body, footer, sections):
    payload = {
        "chatId": chat_id,
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {"button": "Tap to choose", "sections": sections}
        }
    }
    return send_request("/interactive", payload)

def send_request(endpoint, payload):
    try:
        response = requests.post(
            API_URL + endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        response.raise_for_status()
        result = response.json()
        print(f"[DEBUG] {endpoint} → 1MSG response: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] {endpoint} → {e}")
        return {"sent": False, "error": str(e)}
