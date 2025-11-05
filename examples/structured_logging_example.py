"""
Examples of Structured Logging with Structlog, Loguru, and Rich.

This module demonstrates the various features of the enhanced logging system:
- Basic logging (loguru) - backward compatible
- Structured logging (structlog) - with context
- Request tracing
- Performance monitoring
- Context managers
"""

import time
import uuid
from utils.logger import (
    log,  # Original loguru logger
    struct_log,  # New structlog logger
    RequestContext,
    PerformanceContext,
    log_section,
    log_table,
    log_json,
    log_panel,
    log_tree,
)


def example_basic_logging():
    """Examples of basic logging (backward compatible with existing code)"""
    log_section("Basic Logging (Loguru)", "bold cyan")

    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")

    # With context
    log.info(f"User logged in: user_id=123")

    print("\n")


def example_structured_logging():
    """Examples of structured logging with context"""
    log_section("Structured Logging (Structlog)", "bold green")

    # Simple structured log
    struct_log.info("user_logged_in", user_id=123, username="john_doe", ip="192.168.1.1")

    # With nested data
    struct_log.info(
        "api_request_received",
        method="POST",
        path="/api/users",
        headers={"content-type": "application/json"},
        body={"name": "John", "email": "john@example.com"}
    )

    # With performance metrics
    struct_log.info(
        "database_query_completed",
        query="SELECT * FROM users",
        duration_ms=45.2,
        rows_returned=150
    )

    # Sensitive data is automatically censored
    struct_log.info(
        "user_authenticated",
        username="john_doe",
        password="secret123",  # Will be REDACTED
        api_key="sk-1234567890",  # Will be REDACTED
        email="john@example.com"  # Not redacted
    )

    print("\n")


def example_request_context():
    """Examples of request-scoped logging with automatic context"""
    log_section("Request Context Logging", "bold yellow")

    # All logs within this context will include request_id and user_id
    request_id = str(uuid.uuid4())
    with RequestContext(request_id=request_id, user_id="user-456", method="GET", path="/api/weather"):
        struct_log.info("request_started", city="London", country="GB")

        # Simulate some work
        time.sleep(0.1)

        struct_log.info("fetching_weather_data", provider="OpenWeatherMap")

        # Simulate more work
        time.sleep(0.1)

        struct_log.info("request_completed", status_code=200, response_size_bytes=1024)

    # Logs outside the context won't have the request_id
    struct_log.info("background_task_completed", task_name="cleanup")

    print("\n")


def example_performance_context():
    """Examples of performance monitoring"""
    log_section("Performance Monitoring", "bold magenta")

    # Automatically logs operation duration
    with PerformanceContext("database_query", query="SELECT * FROM weather_data WHERE city = ?", city="Madrid"):
        # Simulate expensive operation
        time.sleep(0.15)

    # Nested performance contexts
    with PerformanceContext("api_request", endpoint="/api/weather/London/GB"):
        struct_log.info("validating_request")
        time.sleep(0.05)

        with PerformanceContext("database_lookup", table="weather_cache"):
            time.sleep(0.1)

        with PerformanceContext("external_api_call", provider="OpenWeatherMap"):
            time.sleep(0.2)

    print("\n")


def example_error_logging():
    """Examples of error logging with context"""
    log_section("Error Logging", "bold red")

    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        struct_log.error(
            "division_by_zero_error",
            operation="calculate_average",
            numerator=10,
            denominator=0,
            exc_info=True
        )

    # Error with request context
    with RequestContext(request_id="req-error-123", endpoint="/api/data"):
        try:
            # Simulate error in request processing
            raise ValueError("Invalid input data")
        except ValueError as e:
            struct_log.error(
                "request_processing_error",
                error_message=str(e),
                validation_failed=True,
                exc_info=True
            )

    print("\n")


def example_rich_visualizations():
    """Examples of Rich visual helpers"""
    log_section("Rich Visualizations", "bold blue")

    # Table
    user_data = {
        "user_id": "12345",
        "username": "john_doe",
        "email": "john@example.com",
        "role": "admin",
        "last_login": "2025-11-05 14:30:00"
    }
    log_table("User Information", user_data)

    print("\n")

    # JSON
    api_response = {
        "status": "success",
        "data": {
            "weather": {
                "city": "Madrid",
                "temperature": 22.5,
                "conditions": "sunny"
            }
        },
        "metadata": {
            "request_id": "req-456",
            "timestamp": "2025-11-05T14:30:00Z"
        }
    }
    log_json(api_response, "API Response")

    print("\n")

    # Panel
    log_panel(
        "🚀 Application started successfully!\n"
        "All services are running and ready to accept requests.",
        title="Startup Complete",
        style="green"
    )

    print("\n")

    # Tree
    config_tree = {
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4
        },
        "logging": {
            "level": "INFO",
            "file": "/var/log/app.log",
            "rotation": "10 MB"
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "myapp_db"
        }
    }
    log_tree(config_tree, "Application Configuration")

    print("\n")


def example_combined_logging():
    """Example combining both logging styles"""
    log_section("Combined Logging Example", "bold white")

    # Simulate a complete API request flow
    request_id = f"req-{uuid.uuid4().hex[:8]}"

    with RequestContext(request_id=request_id, client_ip="192.168.1.100"):
        # Use loguru for simple logging
        log.info(f"New request received: {request_id}")

        # Use structlog for structured data
        struct_log.info(
            "request_validated",
            method="GET",
            path="/weather/Madrid/ES",
            user_agent="Python/3.13"
        )

        # Performance monitoring
        with PerformanceContext("weather_api_call", city="Madrid", country="ES"):
            time.sleep(0.12)
            struct_log.info("weather_data_fetched", temperature=25.5, conditions="sunny")

        # More structured logging
        struct_log.info(
            "response_sent",
            status_code=200,
            response_time_ms=125.3,
            cache_hit=False
        )

        # Use Rich visualization
        response_data = {
            "request_id": request_id,
            "status": "200 OK",
            "city": "Madrid",
            "temperature": "25.5°C",
            "response_time": "125.3ms"
        }
        log_table("Request Summary", response_data, style="green")

    print("\n")


def main():
    """Run all examples"""
    log_panel(
        "🎯 Structured Logging Examples\n"
        "Demonstrating Structlog + Loguru + Rich integration",
        title="Example Suite",
        style="bold cyan"
    )

    print("\n")

    # Run examples
    example_basic_logging()
    example_structured_logging()
    example_request_context()
    example_performance_context()
    example_error_logging()
    example_rich_visualizations()
    example_combined_logging()

    log_panel(
        "✨ All examples completed!\n"
        "Check the log files:\n"
        "  - logs/app.log (formatted logs)\n"
        "  - logs/structured.jsonl (JSON structured logs)\n"
        "  - logs/errors.log (errors only)",
        title="Examples Complete",
        style="bold green"
    )


if __name__ == "__main__":
    main()