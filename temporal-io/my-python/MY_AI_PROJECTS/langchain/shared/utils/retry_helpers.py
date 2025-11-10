"""Retry and error handling utilities."""

import asyncio
import logging
from typing import TypeVar, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


def exponential_backoff(
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
) -> Callable[[int], float]:
    """
    Create an exponential backoff function.

    Args:
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential growth

    Returns:
        Function that calculates delay for a given attempt number
    """

    def calculate_delay(attempt: int) -> float:
        delay = base_delay * (exponential_base ** attempt)
        return min(delay, max_delay)

    return calculate_delay


def with_retry(
    max_attempts: int = 3,
    backoff_fn: Callable[[int], float] = None,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_fn: Function to calculate backoff delay
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """
    if backoff_fn is None:
        backoff_fn = exponential_backoff()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = backoff_fn(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    return decorator
