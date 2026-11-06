import logging

from django.conf import settings

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{settings.LOGGER_ROOT_NAME}.{name}")
