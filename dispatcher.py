from flows import bedbug, car_fumigation, mold
from sessions import bedbug_data, car_fumigation_data, mold_removal_data
from services.twilio_client import send_whatsapp_message
from utils import normalize_number

def dispatch_message(request):
    data = request.form.to_dict() if request.form else request.get_json()
    sender = normalize_number(data.get("From", "").replace("whatsapp:", ""))
    message_body = data.get("Body", "").strip()

    # Route to appropriate flow based on ongoing session
    if sender in bedbug_data:
        bedbug.handle_response(sender, message_body)
    elif sender in car_fumigation_data:
        car_fumigation.handle_response(sender, message_body)
    elif sender in mold_removal_data:
        mold.handle_response(sender, message_body)
    else:
        # Start new flows based on keyword triggers
        lowered_body = message_body.lower()
        if "bedbug" in lowered_body:
            bedbug.run_flow(sender)
        elif "fumigation" in lowered_body or "car" in lowered_body:
            car_fumigation.run_flow(sender)
        elif "mold" in lowered_body:
            mold.run_flow(sender)
        else:
            send_whatsapp_message(sender,
                "👋 Welcome! Please clearly reply:\n"
                "1. Bedbug\n"
                "2. Car Fumigation\n"
                "3. Mold Removal"
            )

    return "OK", 200
