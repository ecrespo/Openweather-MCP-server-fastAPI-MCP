"""
Circuit Breaker Implementation.

This module provides a concrete implementation of the Circuit Breaker pattern
for protecting against cascading failures in service calls.
"""

from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import threading
import time
from functools import wraps

from protocols.circuit_breaker_protocols import CircuitBreaker, CircuitState, CircuitBreakerError
from utils.logger import log


class SimpleCircuitBreaker:
    """
    Simple Circuit Breaker implementation.

    This circuit breaker monitors function calls and can temporarily block
    requests if too many failures are detected, giving the failing service
    time to recover.

    :ivar failure_threshold: Number of failures before opening circuit
    :ivar recovery_timeout: Seconds to wait before attempting recovery
    :ivar success_threshold: Number of successes needed to close circuit in HALF_OPEN state
    :ivar state: Current circuit state
    :ivar failure_count: Consecutive failures
    :ivar success_count: Consecutive successes
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        expected_exceptions: tuple = (Exception,)
    ):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait in OPEN state before trying HALF_OPEN
            success_threshold: Consecutive successes needed in HALF_OPEN to close
            expected_exceptions: Tuple of exception types to catch as failures
        """
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold
        self._expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_failures = 0
        self._total_successes = 0
        self._last_failure_time: Optional[datetime] = None
        self._opened_at: Optional[datetime] = None
        self._lock = threading.RLock()

        log.info(
            f"Circuit Breaker initialized: "
            f"failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s, "
            f"success_threshold={success_threshold}"
        )

    @property
    def state(self) -> CircuitState:
        """Get the current state of the circuit breaker."""
        with self._lock:
            self._check_and_update_state()
            return self._state

    @property
    def failure_count(self) -> int:
        """Get the current count of consecutive failures."""
        with self._lock:
            return self._failure_count

    @property
    def success_count(self) -> int:
        """Get the current count of consecutive successes."""
        with self._lock:
            return self._success_count

    def _check_and_update_state(self) -> None:
        """
        Check if circuit should transition from OPEN to HALF_OPEN.

        Called automatically when state is accessed.
        """
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = datetime.now() - self._opened_at
            if elapsed.total_seconds() >= self._recovery_timeout:
                log.info(
                    f"Circuit Breaker transitioning to HALF_OPEN "
                    f"after {elapsed.total_seconds():.1f}s"
                )
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: The function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The return value of func

        Raises:
            CircuitBreakerError: If circuit is OPEN
            Exception: Any exception raised by func
        """
        with self._lock:
            current_state = self.state

            if current_state == CircuitState.OPEN:
                retry_after = None
                if self._opened_at:
                    elapsed = (datetime.now() - self._opened_at).total_seconds()
                    retry_after = max(0, self._recovery_timeout - elapsed)

                log.warning(
                    f"Circuit Breaker is OPEN, blocking call to {func.__name__}. "
                    f"Retry after {retry_after:.1f}s"
                )
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN. Retry after {retry_after:.1f}s",
                    retry_after=retry_after
                )

        # Execute the function outside the lock
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except self._expected_exceptions as e:
            self.record_failure()
            raise

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self._total_successes += 1
            self._failure_count = 0
            self._success_count += 1

            if self._state == CircuitState.HALF_OPEN:
                if self._success_count >= self._success_threshold:
                    log.info(
                        f"Circuit Breaker closing after "
                        f"{self._success_count} successful calls"
                    )
                    self._state = CircuitState.CLOSED
                    self._success_count = 0
                    self._opened_at = None

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._total_failures += 1
            self._success_count = 0
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                log.warning(
                    "Circuit Breaker reopening after failure in HALF_OPEN state"
                )
                self._state = CircuitState.OPEN
                self._opened_at = datetime.now()
                self._failure_count = 0

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self._failure_threshold:
                    log.error(
                        f"Circuit Breaker opening after "
                        f"{self._failure_count} consecutive failures"
                    )
                    self._state = CircuitState.OPEN
                    self._opened_at = datetime.now()
                    self._failure_count = 0

    def reset(self) -> None:
        """Reset the circuit breaker to CLOSED state."""
        with self._lock:
            log.info("Circuit Breaker manually reset to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._opened_at = None

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the circuit breaker."""
        with self._lock:
            self._check_and_update_state()

            stats = {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "total_failures": self._total_failures,
                "total_successes": self._total_successes,
                "failure_threshold": self._failure_threshold,
                "recovery_timeout": self._recovery_timeout,
                "success_threshold": self._success_threshold,
            }

            if self._last_failure_time:
                stats["last_failure_time"] = self._last_failure_time.isoformat()

            if self._opened_at:
                stats["opened_at"] = self._opened_at.isoformat()
                elapsed = (datetime.now() - self._opened_at).total_seconds()
                stats["time_open"] = elapsed
                stats["retry_after"] = max(0, self._recovery_timeout - elapsed)

            # Calculate success rate
            total_calls = self._total_successes + self._total_failures
            if total_calls > 0:
                stats["success_rate"] = self._total_successes / total_calls
            else:
                stats["success_rate"] = 1.0

            return stats


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
    expected_exceptions: tuple = (Exception,)
):
    """
    Decorator to apply circuit breaker pattern to a function.

    Usage:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30.0)
        def call_external_api():
            # ... make API call

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        success_threshold: Successes needed to close circuit
        expected_exceptions: Exception types to catch as failures

    Returns:
        Decorated function with circuit breaker protection
    """
    breaker = SimpleCircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold,
        expected_exceptions=expected_exceptions
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        # Attach breaker to function for introspection
        wrapper.circuit_breaker = breaker
        return wrapper

    return decorator


class CircuitBreakerRegistry:
    """
    Registry to manage multiple circuit breakers.

    Allows centralized monitoring and management of all circuit breakers
    in the application.
    """

    def __init__(self):
        """Initialize the circuit breaker registry."""
        self._breakers: dict[str, SimpleCircuitBreaker] = {}
        self._lock = threading.Lock()

    def register(self, name: str, breaker: SimpleCircuitBreaker) -> None:
        """
        Register a circuit breaker.

        Args:
            name: Unique name for the circuit breaker
            breaker: The circuit breaker instance
        """
        with self._lock:
            self._breakers[name] = breaker
            log.debug(f"Circuit Breaker '{name}' registered")

    def get(self, name: str) -> Optional[SimpleCircuitBreaker]:
        """
        Get a circuit breaker by name.

        Args:
            name: Name of the circuit breaker

        Returns:
            The circuit breaker instance, or None if not found
        """
        with self._lock:
            return self._breakers.get(name)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get statistics for all registered circuit breakers.

        Returns:
            Dictionary mapping breaker names to their stats
        """
        with self._lock:
            return {
                name: breaker.get_stats()
                for name, breaker in self._breakers.items()
            }

    def reset_all(self) -> None:
        """Reset all circuit breakers to CLOSED state."""
        with self._lock:
            for name, breaker in self._breakers.items():
                breaker.reset()
                log.info(f"Circuit Breaker '{name}' reset")

    def list_breakers(self) -> list[str]:
        """
        Get list of all registered circuit breaker names.

        Returns:
            List of circuit breaker names
        """
        with self._lock:
            return list(self._breakers.keys())


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()