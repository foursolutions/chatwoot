# dispatcher.py
from flows import bedbug, car_fumigation, mold
from sessions import bedbug_data, car_fumigation_data, mold_removal_data

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
    body = request.values.get("Body", "").strip().lower()

    # --- DEBUGGING: Print session data every time a message is received ---
    print("=== DEBUG: bedbug_data:", bedbug_data)
    print("=== DEBUG: car_fumigation_data:", car_fumigation_data)
    print("=== DEBUG: mold_removal_data:", mold_removal_data)
    print("=== Incoming from:", from_number, "body:", body)
    # ----------------------------------------------------------------------

    # 1. Universal menu command: always resets all sessions and shows main menu
    if body == "menu":
        reset_session(from_number)
        return send_main_menu(from_number)

    # 2. If already in a car fumigation flow, always continue car fumigation!
    if from_number in car_fumigation_data:
        car_fumigation.handle_response(from_number, body)
        return "OK"

    # 3. If already in bedbug flow, continue bedbug!
    if from_number in bedbug_data:
        bedbug.handle_response(from_number, body)
        return "OK"

    # 4. If already in mold flow, continue mold!
    if from_number in mold_removal_data:
        mold.handle_response(from_number, body)
        return "OK"

    # 5. Not in a flow: interpret as main menu selection
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


