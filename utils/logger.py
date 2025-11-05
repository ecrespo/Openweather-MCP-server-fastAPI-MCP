"""
Enhanced Logging System with Structlog, Loguru, and Rich integration.

This module provides a comprehensive logging solution that combines:
- structlog for structured logging with context
- loguru for powerful file rotation and formatting
- rich for beautiful console output

Features:
- Structured logging with automatic context propagation
- Beautiful console output with syntax highlighting
- File rotation and compression
- JSON logging support
- Request tracing and correlation IDs
- Performance metrics logging
- Rich visual helpers (tables, trees, panels, etc.)
"""

import sys
import contextvars
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Loguru imports
from loguru import logger as loguru_logger

# Rich imports
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback
from rich.theme import Theme
from rich.markup import escape

# Structlog imports
import structlog
from structlog.types import EventDict, WrappedLogger

from utils.config import settings

# Install Rich traceback for better error messages
install_rich_traceback(show_locals=True)

# Custom theme for logs
custom_theme = Theme({
    "log.time": "dim cyan",
    "log.message": "white",
    "log.path": "dim blue",
    "logging.level.debug": "dim blue",
    "logging.level.info": "green",
    "logging.level.warning": "yellow",
    "logging.level.error": "bold red",
    "logging.level.critical": "bold white on red",
    "log.level": "bold",
})

# Rich console for output
console = Console(theme=custom_theme)

# Context vars for request tracing
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "user_id", default=None
)


class RichLogHandler:
    """
    Handles logging with Rich console.

    This class provides a mechanism to display log messages using the Rich library's
    `Console`. It ensures that messages are properly formatted and displayed on the
    Rich console instance.

    :ivar console: The Rich console instance used for displaying log messages.
    :type console: Console
    """

    def __init__(self, console: Console):
        self.console = console

    def write(self, message):
        """Write message using Rich"""
        message = message.rstrip()
        if message:
            self.console.print(message, markup=True, highlight=False)


def format_record(record: dict) -> str:
    """
    Formats a record dictionary into a color-coded and structured log string.

    The function takes a record dictionary containing log information, such as the log level,
    timestamp, file, function details, and message, and produces a formatted string with
    colors for terminal logging.

    :param record: A dictionary containing log record details. It includes the level,
                   timestamp, file name, function name, line number, and the log message.
    :type record: dict
    :return: A formatted string with color-coded log information for terminal output.
    :rtype: str
    """
    level_colors = {
        "TRACE": "dim blue",
        "DEBUG": "cyan",
        "INFO": "green",
        "SUCCESS": "bold green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold white on red"
    }

    level = record["level"].name
    level_color = level_colors.get(level, "white")

    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    file_info = f"{record['name']}:{record['function']}:{record['line']}"
    # Escape both Rich markup AND format string placeholders (curly braces)
    message = escape(str(record["message"])).replace("{", "{{").replace("}", "}}")

    formatted = (
        f"[dim cyan]{timestamp}[/dim cyan] | "
        f"[{level_color}]{level: <8}[/{level_color}] | "
        f"[dim blue]{file_info}[/dim blue] - "
        f"[white]{message}[/white]"
    )

    return formatted


# ============================================================================
# Structlog Integration
# ============================================================================

class LoguruWriter:
    """
    Adapter to write structlog events to loguru.

    This bridges structlog's structured logging with loguru's powerful
    output handling and file management.
    """

    def write(self, message: str) -> None:
        """Write structured log message to loguru"""
        loguru_logger.opt(depth=2, raw=True).info(message + "\n")

    def flush(self) -> None:
        """Flush is a no-op for loguru"""
        pass


def add_timestamp(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add ISO timestamp to log event"""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def add_log_level_name(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add log level name from method_name"""
    event_dict["level"] = method_name.upper()
    return event_dict


def add_context_vars(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add context variables (request_id, user_id) to log events"""
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id

    user_id = user_id_var.get()
    if user_id:
        event_dict["user_id"] = user_id

    return event_dict


def add_caller_info(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add caller file and line information"""
    # Get frame info from structlog
    frame_info = event_dict.get("_frame_info")
    if frame_info:
        event_dict["file"] = frame_info[0]
        event_dict["line"] = frame_info[1]
        event_dict["function"] = frame_info[2]

    return event_dict


def censor_sensitive_data(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Censor sensitive data like passwords and tokens"""
    sensitive_keys = {
        "password", "passwd", "pwd", "secret", "token",
        "api_key", "apikey", "access_token", "auth"
    }

    def _censor_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively censor sensitive keys in dictionaries"""
        censored = {}
        for key, value in d.items():
            if isinstance(value, dict):
                censored[key] = _censor_dict(value)
            elif any(sensitive in key.lower() for sensitive in sensitive_keys):
                censored[key] = "***REDACTED***"
            else:
                censored[key] = value
        return censored

    # Censor event_dict keys
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***REDACTED***"
        elif isinstance(event_dict[key], dict):
            event_dict[key] = _censor_dict(event_dict[key])

    return event_dict


def setup_structlog() -> structlog.BoundLogger:
    """
    Configure structlog with processors and loguru as backend.

    This sets up the structlog pipeline with various processors for:
    - Adding timestamps
    - Adding log levels
    - Adding context variables (request_id, user_id)
    - Censoring sensitive data
    - JSON rendering for structured output

    Returns:
        Configured structlog logger instance
    """
    structlog.configure(
        processors=[
            # Merge context from thread-local or context vars
            structlog.contextvars.merge_contextvars,
            # Add timestamp
            add_timestamp,
            # Add log level from method name
            add_log_level_name,
            # Add context vars (request_id, user_id)
            add_context_vars,
            # Add stack info if requested
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.processors.format_exc_info,
            # Censor sensitive data
            censor_sensitive_data,
            # Decode unicode
            structlog.processors.UnicodeDecoder(),
            # Add caller info
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ],
            ),
            # Final rendering - JSON for structured logs
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=LoguruWriter()),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


def setup_loguru():
    """
    Configure loguru with multiple handlers.

    Sets up:
    - Console handler with Rich formatting
    - File handler with rotation and compression
    - Error-only file handler

    Returns:
        Configured loguru logger
    """
    loguru_logger.remove()

    # Handler for console with Rich
    rich_handler = RichLogHandler(console)

    loguru_logger.add(
        rich_handler.write,
        format=format_record,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Handler for file
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    loguru_logger.add(
        settings.LOG_FILE,
        format=file_format,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Handler for errors
    error_log_file = log_path.parent / "errors.log"

    loguru_logger.add(
        str(error_log_file),
        format=file_format,
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # JSON structured log file
    json_log_file = log_path.parent / "structured.jsonl"
    loguru_logger.add(
        str(json_log_file),
        format="{message}",  # Raw JSON from structlog
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
        serialize=False,  # Already JSON from structlog
    )

    loguru_logger.info("✨ Logger configurado con Structlog, Rich y Loguru")
    loguru_logger.debug(f"📁 Logs guardados en: {settings.LOG_FILE}")
    loguru_logger.debug(f"📊 Nivel de log: {settings.LOG_LEVEL}")

    return loguru_logger


# ============================================================================
# Context Managers for Request Tracing
# ============================================================================

class RequestContext:
    """
    Context manager for request-scoped logging.

    Automatically adds request_id and other metadata to all logs
    within the context.

    Example:
        with RequestContext(request_id="req-123", user_id="user-456"):
            log.info("Processing request", action="upload")
            # This log will include request_id and user_id automatically
    """

    def __init__(self, request_id: Optional[str] = None, user_id: Optional[str] = None, **extra):
        self.request_id = request_id
        self.user_id = user_id
        self.extra = extra
        self._tokens = []

    def __enter__(self):
        if self.request_id:
            token = request_id_var.set(self.request_id)
            self._tokens.append(("request_id", token))

        if self.user_id:
            token = user_id_var.set(self.user_id)
            self._tokens.append(("user_id", token))

        # Bind extra context to structlog
        if self.extra:
            structlog.contextvars.bind_contextvars(**self.extra)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset context vars
        for var_name, token in self._tokens:
            if var_name == "request_id":
                request_id_var.reset(token)
            elif var_name == "user_id":
                user_id_var.reset(token)

        # Clear structlog context
        if self.extra:
            structlog.contextvars.clear_contextvars()

        return False


class PerformanceContext:
    """
    Context manager for performance logging.

    Automatically logs execution time of a code block.

    Example:
        with PerformanceContext("database_query", query="SELECT * FROM users"):
            # ... expensive operation ...
            pass
        # Logs: operation="database_query", duration_ms=123.45
    """

    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        struct_log.debug("operation_started", operation=self.operation, **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration_ms = (time.perf_counter() - self.start_time) * 1000

        if exc_type is None:
            struct_log.info(
                "operation_completed",
                operation=self.operation,
                duration_ms=round(duration_ms, 2),
                status="success",
                **self.context
            )
        else:
            struct_log.error(
                "operation_failed",
                operation=self.operation,
                duration_ms=round(duration_ms, 2),
                status="error",
                error_type=exc_type.__name__,
                **self.context
            )

        return False


# ============================================================================
# Rich Visual Helpers (Original functionality preserved)
# ============================================================================

def log_section(title: str, style: str = "bold cyan"):
    """Log a section divider with title"""
    console.rule(f"[{style}]{title}[/{style}]")


def log_table(title: str, data: dict, style: str = "cyan"):
    """
    Logs a table with specified title, data, and style using the rich library.

    This function creates a table using the `rich.table.Table` class, adds the
    provided data as rows, and prints it to the console. The table's visual
    appearance can be customized with a title and a color style.

    :param title: The title of the table to display.
    :type title: str
    :param data: A dictionary where each key-value pair represents a row in
                 the table. Keys are displayed as column entries under "Campo,"
                 and values under "Valor."
    :type data: dict
    :param style: (Optional) The color style to apply to the table's title.
                  Defaults to "cyan".
    :type style: str
    :return: None
    """
    from rich.table import Table

    table = Table(title=title, style=style)
    table.add_column("Campo", style="cyan", no_wrap=True)
    table.add_column("Valor", style="white")

    for key, value in data.items():
        table.add_row(str(key), str(value))

    console.print(table)


def log_json(data: dict, title: str = "JSON Data"):
    """
    Logs a JSON-compatible Python dictionary to the console in a structured and
    formatted manner. This function employs the `rich` library for displaying
    the data with enhanced readability.

    :param data: A dictionary containing JSON-compatible data to be logged.
    :type data: dict
    :param title: A string specifying the title to be displayed above the JSON
        data in the console. Defaults to "JSON Data".
    :type title: str, optional
    :return: None
    """
    from rich.json import JSON

    console.print(f"[bold cyan]{title}:[/bold cyan]")
    console.print(JSON.from_data(data))


def log_panel(message: str, title: str = None, style: str = "cyan"):
    """
    Logs a styled message to the console within a Rich panel.

    This function uses the Rich library to create a visually appealing panel
    in the console. The message can be styled and optionally titled, providing
    a clear and organized output for console applications.

    :param message: The main content of the panel to be displayed in the console.
    :type message: str
    :param title: An optional title for the panel.
    :type title: str, optional
    :param style: The styling applied to the panel. Defaults to 'cyan'.
    :type style: str, optional
    :return: None
    """
    from rich.panel import Panel

    console.print(Panel(message, title=title, style=style))


def log_tree(data: dict, title: str = "Tree View"):
    """
    Log a hierarchical tree structure to the console. This function utilizes the `rich`
    library to visually represent nested data, such as dictionaries or lists, in a
    tree-like format for readability.

    :param data: A dictionary or list containing the hierarchical data structure
        to be logged as a tree.
    :type data: dict
    :param title: An optional title for the tree representation. Defaults to "Tree View".
    :type title: str
    :return: None
    """
    from rich.tree import Tree

    def add_to_tree(tree, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    branch = tree.add(f"[cyan]{key}[/cyan]")
                    add_to_tree(branch, value)
                else:
                    tree.add(f"[cyan]{key}[/cyan]: [white]{value}[/white]")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    branch = tree.add(f"[yellow][{i}][/yellow]")
                    add_to_tree(branch, item)
                else:
                    tree.add(f"[yellow][{i}][/yellow]: [white]{item}[/white]")

    tree = Tree(f"[bold]{title}[/bold]")
    add_to_tree(tree, data)
    console.print(tree)


def log_status(message: str, spinner: str = "dots"):
    """
    Logs a status message with an optional spinner indicator. The function uses the
    provided message and spinner type to display a styled status.

    :param message: The status message to be logged.
    :type message: str
    :param spinner: The type of spinner to display alongside the message. Default
        is "dots".
    :type spinner: str
    :return: A console status object representing the logged status.
    :rtype: object
    """
    return console.status(message, spinner=spinner)


class LogContext:
    """
    Provides a context manager for logging sections with a specified title and style.

    This class simplifies logging by marking the beginning and the end of a
    specific code section. It supports customizable styles for text formatting
    and ensures that any exceptions raised within the context are also logged
    appropriately.

    :ivar title: The title of the log section.
    :type title: str
    :ivar style: The style of the log section's title. Defaults to "cyan".
    :type style: str
    """

    def __init__(self, title: str, style: str = "cyan"):
        self.title = title
        self.style = style

    def __enter__(self):
        log_section(f"BEGIN: {self.title}", self.style)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            log_section(f"END: {self.title} ✓", "green")
        else:
            log_section(f"END: {self.title} ✗", "red")
        return False


# ============================================================================
# Initialize Loggers
# ============================================================================

# Setup loguru first (backend)
log = setup_loguru()

# Setup structlog (structured logging frontend)
struct_log = setup_structlog()

__all__ = [
    # Loguru logger (original)
    'log',
    # Structlog logger (structured)
    'struct_log',
    # Rich console
    'console',
    # Context managers
    'RequestContext',
    'PerformanceContext',
    'LogContext',
    # Context vars
    'request_id_var',
    'user_id_var',
    # Visual helpers
    'log_section',
    'log_table',
    'log_json',
    'log_panel',
    'log_tree',
    'log_status',
]