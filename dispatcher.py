# dispatcher.py
from flows import bedbug, car_fumigation, mold
from sessions import live_sessions, bedbug_data, car_fumigation_data, mold_removal_data

MAIN_MENU = (
    "👋 Welcome to Four Solutions Live Assist!\n"
    "How can we help you today? Reply with a number:\n"
    "1. Bedbug Service\n"
    "2. Car Fumigation\n"
    "3. Mold Removal\n"
    "Type 'menu' at any time to return to this menu."
)

def dispatch_message(request):
    from_number = request.values.get("From")
    body = request.values.get("Body", "").strip()

    # Menu reset
    if body.lower() == "menu":
        reset_session(from_number)
        return send_main_menu(from_number)

    # 1. If in a car fumigation session, route to car fumigation!
    if from_number in car_fumigation_data:
        car_fumigation.handle_response(from_number, body)
        return "OK"
    # 2. If in a bedbug session, route to bedbug
    if from_number in bedbug_data:
        bedbug.handle_response(from_number, body)
        return "OK"
    # 3. If in a mold session, route to mold
    if from_number in mold_removal_data:
        mold.handle_response(from_number, body)
        return "OK"

    # 4. Only if NOT in a session, check for menu triggers!
    if body in ["1", "bedbug"]:
        bedbug.run_flow(from_number)
    elif body in ["2", "car fumigation", "car"]:
        car_fumigation.run_flow(from_number)
    elif body in ["3", "mold", "mold removal"]:
        mold.run_flow(from_number)
    else:
        send_main_menu(from_number)
    return "OK"

def reset_session(from_number):
    bedbug_data.pop(from_number, None)
    car_fumigation_data.pop(from_number, None)
    mold_removal_data.pop(from_number, None)

def send_main_menu(to):
    from services.twilio_client import send_whatsapp_message
    send_whatsapp_message(to, MAIN_MENU)
