# utils.py
import re
def normalize_number(number):
    number = re.sub(r"\s+", "", number)
    if not number.startswith("+"):
        number = "+" + number
    return number