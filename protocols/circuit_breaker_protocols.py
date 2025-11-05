"""
Circuit Breaker Protocol for Resilient Service Calls.

This module defines the protocol for Circuit Breaker implementations,
which help prevent cascading failures by detecting and isolating failing
services.
"""

from typing import Protocol, Callable, Any, Optional
from enum import Enum


class CircuitState(Enum):
    """
    Enum representing the possible states of a Circuit Breaker.

    CLOSED: Circuit is working normally, requests pass through
    OPEN: Circuit has detected failures, requests are blocked
    HALF_OPEN: Circuit is testing if the service has recovered
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker(Protocol):
    """
    Protocol for Circuit Breaker implementations.

    A Circuit Breaker monitors calls to external services and can temporarily
    block requests if the service appears to be failing, giving it time to
    recover. This prevents cascading failures and resource exhaustion.

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Too many failures detected, requests are blocked
        - HALF_OPEN: Testing if service has recovered

    Transitions:
        - CLOSED -> OPEN: After failure_threshold consecutive failures
        - OPEN -> HALF_OPEN: After recovery_timeout seconds
        - HALF_OPEN -> CLOSED: After success_threshold consecutive successes
        - HALF_OPEN -> OPEN: On any failure

    Example implementations:
        - SimpleCircuitBreaker: Basic circuit breaker with failure counting
        - TimeWindowCircuitBreaker: Counts failures within time windows
        - AdaptiveCircuitBreaker: Adjusts thresholds based on patterns
    """

    @property
    def state(self) -> CircuitState:
        """
        Get the current state of the circuit breaker.

        Returns:
            The current CircuitState (CLOSED, OPEN, or HALF_OPEN)
        """
        ...

    @property
    def failure_count(self) -> int:
        """
        Get the current count of consecutive failures.

        Returns:
            Number of consecutive failures
        """
        ...

    @property
    def success_count(self) -> int:
        """
        Get the current count of consecutive successes.

        Returns:
            Number of consecutive successes
        """
        ...

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function through the circuit breaker.

        The circuit breaker will:
        1. Check if the circuit is OPEN - if so, raise CircuitBreakerError
        2. Execute the function
        3. Record success or failure
        4. Update circuit state accordingly

        Args:
            func: The function to execute
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            The return value of func if successful

        Raises:
            CircuitBreakerError: If the circuit is OPEN
            Exception: Any exception raised by func (also recorded as failure)
        """
        ...

    def record_success(self) -> None:
        """
        Record a successful call.

        Updates the circuit breaker's state based on the success.
        May transition from HALF_OPEN to CLOSED if enough successes.
        """
        ...

    def record_failure(self) -> None:
        """
        Record a failed call.

        Updates the circuit breaker's state based on the failure.
        May transition from CLOSED to OPEN if too many failures.
        """
        ...

    def reset(self) -> None:
        """
        Reset the circuit breaker to CLOSED state.

        Clears all failure and success counts.
        Useful for manual intervention or testing.
        """
        ...

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the circuit breaker.

        Returns:
            Dictionary containing:
                - state: Current circuit state
                - failure_count: Number of consecutive failures
                - success_count: Number of consecutive successes
                - total_failures: Total failures since creation/reset
                - total_successes: Total successes since creation/reset
                - last_failure_time: Timestamp of last failure (if any)
                - opened_at: Timestamp when circuit opened (if OPEN)
                - Additional implementation-specific stats
        """
        ...


class CircuitBreakerError(Exception):
    """
    Exception raised when a circuit breaker is OPEN.

    This exception indicates that the circuit breaker has detected
    too many failures and is temporarily blocking requests to give
    the failing service time to recover.
    """

    def __init__(
        self,
        message: str = "Circuit breaker is OPEN",
        retry_after: Optional[float] = None
    ):
        """
        Initialize the CircuitBreakerError.

        Args:
            message: Error message
            retry_after: Seconds until the circuit may attempt recovery
        """
        self.retry_after = retry_after
        super().__init__(message)