# sessions.py
live_sessions = {}
car_fumigation_data = {}
mold_removal_data = {}
bedbug_data = {}
last_message_id = {}
admin_targets = {}

def reset_session(from_number):
    bedbug_data.pop(from_number, None)
    car_fumigation_data.pop(from_number, None)
    mold_removal_data.pop(from_number, None)
