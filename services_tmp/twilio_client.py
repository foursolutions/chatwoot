# services/twilio_client.py
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
from twilio.rest import Client

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to, body):
    to = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
    try:
        message = twilio_client.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=to,
            body=body
        )
        print(f"Message sent: {message.sid}")
    except Exception as e:
        print(f"Twilio send failed: {e}")
