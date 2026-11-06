import time
import ulid

def generate_ulid() -> str:
    """
    Generates id with ulid-py
    """
    return ulid.new().str

def generate_trx_id() -> str:
    """
    Generates trx id with timestamp
    """
    return "IB" + str(time.time()).replace(".", "")[0:14]