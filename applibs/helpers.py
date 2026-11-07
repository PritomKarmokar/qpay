import time
import ulid
import json
import hashlib

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

def clean_phone_number(phone_number: str) -> str:
    if str(phone_number).startswith("+88"):
        phone_number = str(phone_number).replace("+88", "")
    elif str(phone_number).startswith("88"):
        phone_number = "".join(list(phone_number)[2:])
    elif str(phone_number[1:]).find("+") != "-1":
        phone_number = phone_number.replace("+", "")

    phone_number = phone_number.replace("-", "")

    return phone_number

def generate_request_hash(payload: dict) -> str:
    serialized_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized_payload.encode("utf-8")
    ).hexdigest()