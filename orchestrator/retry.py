from utils.logger import logger
import time

def retry_with_feedback(
    fn,
    max_retries=3,
    retry_delay=2,
    name="step",
):
    """
    Retries a function that may throw an exception.
    The function itself should incorporate feedback if needed.
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"{name}: attempt {attempt}/{max_retries}")
            return fn()
        except Exception as e:
            last_error = e
            logger.warning(f"{name} failed: {e}")

            if attempt < max_retries:
                time.sleep(retry_delay)

    raise RuntimeError(
        f"{name} failed after {max_retries} retries"
    ) from last_error
