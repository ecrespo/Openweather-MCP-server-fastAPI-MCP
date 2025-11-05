"""
Tests for Circuit Breaker implementation.
"""

import pytest
import time
from datetime import datetime

from utils.circuit_breaker import SimpleCircuitBreaker, CircuitState, CircuitBreakerError


def test_circuit_breaker_closed_state():
    """Test that circuit breaker starts in CLOSED state."""
    breaker = SimpleCircuitBreaker()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.success_count == 0


def test_circuit_breaker_successful_call():
    """Test successful function call through circuit breaker."""
    breaker = SimpleCircuitBreaker()

    def successful_function():
        return "success"

    result = breaker.call(successful_function)
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_opens_after_failures():
    """Test that circuit breaker opens after threshold failures."""
    breaker = SimpleCircuitBreaker(failure_threshold=3)

    def failing_function():
        raise Exception("Test failure")

    # Cause 3 failures
    for i in range(3):
        with pytest.raises(Exception):
            breaker.call(failing_function)

    # Circuit should be OPEN
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_blocks_when_open():
    """Test that circuit breaker blocks calls when OPEN."""
    breaker = SimpleCircuitBreaker(failure_threshold=2)

    def failing_function():
        raise Exception("Test failure")

    # Cause 2 failures to open circuit
    for i in range(2):
        with pytest.raises(Exception):
            breaker.call(failing_function)

    assert breaker.state == CircuitState.OPEN

    # Next call should be blocked
    def successful_function():
        return "success"

    with pytest.raises(CircuitBreakerError) as exc_info:
        breaker.call(successful_function)

    assert "Circuit breaker is OPEN" in str(exc_info.value)


def test_circuit_breaker_half_open_after_timeout():
    """Test that circuit breaker transitions to HALF_OPEN after timeout."""
    breaker = SimpleCircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.1  # 100ms for testing
    )

    def failing_function():
        raise Exception("Test failure")

    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            breaker.call(failing_function)

    assert breaker.state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.15)

    # Check state - should be HALF_OPEN
    assert breaker.state == CircuitState.HALF_OPEN


def test_circuit_breaker_closes_after_successful_recovery():
    """Test that circuit breaker closes after successful recovery."""
    breaker = SimpleCircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.1,
        success_threshold=2
    )

    def failing_function():
        raise Exception("Test failure")

    def successful_function():
        return "success"

    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            breaker.call(failing_function)

    assert breaker.state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.15)
    assert breaker.state == CircuitState.HALF_OPEN

    # Make 2 successful calls
    result1 = breaker.call(successful_function)
    assert result1 == "success"
    assert breaker.state == CircuitState.HALF_OPEN

    result2 = breaker.call(successful_function)
    assert result2 == "success"
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_reopens_on_failure_in_half_open():
    """Test that circuit breaker reopens if failure occurs in HALF_OPEN."""
    breaker = SimpleCircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.1
    )

    def failing_function():
        raise Exception("Test failure")

    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            breaker.call(failing_function)

    assert breaker.state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.15)
    assert breaker.state == CircuitState.HALF_OPEN

    # Failure in HALF_OPEN should reopen
    with pytest.raises(Exception):
        breaker.call(failing_function)

    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_reset():
    """Test manual reset of circuit breaker."""
    breaker = SimpleCircuitBreaker(failure_threshold=2)

    def failing_function():
        raise Exception("Test failure")

    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            breaker.call(failing_function)

    assert breaker.state == CircuitState.OPEN

    # Reset
    breaker.reset()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_stats():
    """Test circuit breaker statistics."""
    breaker = SimpleCircuitBreaker(failure_threshold=3)

    def successful_function():
        return "success"

    def failing_function():
        raise Exception("Test failure")

    # Mix of successes and failures
    breaker.call(successful_function)
    breaker.call(successful_function)

    try:
        breaker.call(failing_function)
    except Exception:
        pass

    stats = breaker.get_stats()

    assert stats["state"] == "closed"
    assert stats["total_successes"] == 2
    assert stats["total_failures"] == 1
    assert stats["failure_count"] == 1
    assert "success_rate" in stats
    assert stats["success_rate"] == 2/3


def test_circuit_breaker_with_specific_exceptions():
    """Test circuit breaker with specific exception types."""
    breaker = SimpleCircuitBreaker(
        failure_threshold=2,
        expected_exceptions=(ValueError,)
    )

    def value_error_function():
        raise ValueError("Test error")

    def type_error_function():
        raise TypeError("Test error")

    # ValueError should count as failure
    with pytest.raises(ValueError):
        breaker.call(value_error_function)

    assert breaker.failure_count == 1

    # TypeError should not count (not in expected_exceptions)
    with pytest.raises(TypeError):
        breaker.call(type_error_function)

    # Failure count should NOT increase
    assert breaker.failure_count == 0  # Reset after success
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_concurrent_access():
    """Test that circuit breaker is thread-safe."""
    import threading

    breaker = SimpleCircuitBreaker()
    results = []
    errors = []

    def successful_function():
        return "success"

    def call_breaker():
        try:
            result = breaker.call(successful_function)
            results.append(result)
        except Exception as e:
            errors.append(e)

    # Create multiple threads
    threads = [threading.Thread(target=call_breaker) for _ in range(10)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # All should succeed
    assert len(results) == 10
    assert len(errors) == 0
    assert all(r == "success" for r in results)


def test_circuit_breaker_retry_after():
    """Test that CircuitBreakerError includes retry_after information."""
    breaker = SimpleCircuitBreaker(
        failure_threshold=1,
        recovery_timeout=30.0
    )

    def failing_function():
        raise Exception("Test failure")

    # Open the circuit
    with pytest.raises(Exception):
        breaker.call(failing_function)

    assert breaker.state == CircuitState.OPEN

    # Try to call - should get CircuitBreakerError with retry_after
    try:
        breaker.call(failing_function)
        assert False, "Should have raised CircuitBreakerError"
    except CircuitBreakerError as e:
        assert e.retry_after is not None
        assert e.retry_after <= 30.0
        assert e.retry_after >= 29.0  # Should be close to 30


def test_circuit_breaker_time_open():
    """Test that stats include time_open when circuit is OPEN."""
    breaker = SimpleCircuitBreaker(
        failure_threshold=1,
        recovery_timeout=30.0
    )

    def failing_function():
        raise Exception("Test failure")

    # Open the circuit
    with pytest.raises(Exception):
        breaker.call(failing_function)

    time.sleep(0.1)  # Wait a bit

    stats = breaker.get_stats()
    assert stats["state"] == "open"
    assert "time_open" in stats
    assert stats["time_open"] >= 0.1
    assert "retry_after" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])