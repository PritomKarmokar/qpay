import re

MOBILE_REGEX = re.compile(r"^(?:\+?88)?01[1-9][0-9]{8}$")

def is_phone_valid(phone_number):
    """
    Check phone number is valid or not.

    @return: Boolean
    """
    if phone_number:
        if MOBILE_REGEX.match(phone_number):
            return True
        else:
            return False
    else:
        return False
