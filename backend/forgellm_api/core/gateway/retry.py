import asyncio
import logging
from typing import Callable, Any
from fastapi import HTTPException
import httpx

logger = logging.getLogger(__name__)


async def with_retry_and_fallback(
    operation: Callable[[], Any],
    fallback_operation: Callable[[], Any] = None,
    max_retries: int = 2,
    base_delay: float = 0.5,
) -> Any:
    """
    Executes an operation with exponential backoff retries.
    If it fails completely, attempts the fallback_operation.
    Only retries transient failures.
    """
    retries = 0
    while True:
        try:
            return await operation()
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.WriteError,
        ) as e:
            # Transient networking errors
            retries += 1
            if retries > max_retries:
                logger.warning(
                    f"Operation failed after {max_retries} retries: {str(e)}"
                )
                break

            delay = base_delay * (2 ** (retries - 1))
            logger.info(
                f"Transient error occurred: {str(e)}. Retrying in {delay}s (Attempt {retries}/{max_retries})"
            )
            await asyncio.sleep(delay)

        except HTTPException as e:
            # 5xx errors are transient server errors. 4xx are client errors (do not retry).
            if 500 <= e.status_code < 600:
                retries += 1
                if retries > max_retries:
                    logger.warning(
                        f"Operation failed with 5xx error after {max_retries} retries: {e.detail}"
                    )
                    break

                delay = base_delay * (2 ** (retries - 1))
                logger.info(
                    f"5xx Server Error: {e.detail}. Retrying in {delay}s (Attempt {retries}/{max_retries})"
                )
                await asyncio.sleep(delay)
            else:
                # 4xx Error, don't retry, don't fallback. Just raise.
                raise
        except Exception as e:
            # Unknown exception
            logger.error(f"Unexpected error during operation: {str(e)}")
            break

    # If we exit the loop, primary failed entirely.
    if fallback_operation:
        logger.info("Primary operation failed. Attempting fallback routing.")
        try:
            # Fallback doesn't get retries in this simple implementation
            return await fallback_operation()
        except Exception as fallback_err:
            logger.error(f"Fallback operation also failed: {str(fallback_err)}")
            raise HTTPException(
                status_code=502,
                detail="Bad Gateway: Primary and Fallback models failed.",
            )

    raise HTTPException(
        status_code=503,
        detail="Service Unavailable: Model failed to process request and no fallback configured.",
    )
