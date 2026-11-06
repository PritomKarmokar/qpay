import time
from functools import wraps

from applibs.logger import get_logger

logger = get_logger(__name__)

def measure_execution_time(func=None, *, step: str | None = None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                return f(*args, **kwargs)
            finally:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.info({
                    "step": step or f.__name__,
                    "message": "Execution completed",
                    "elapsed_ms": elapsed_ms,
                })
        return wrapper

    # Used as @measure_execution_time (no parentheses)
    if func is not None:
        return decorator(func)

    # Used as @measure_execution_time() or @measure_execution_time(step="...")
    return decorator
