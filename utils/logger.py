import sys
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback
from rich.theme import Theme
from rich.markup import escape
from utils.config import settings

# Instalar Rich traceback para mejores mensajes de error
install_rich_traceback(show_locals=True)

# Tema personalizado para los logs
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

# Console de Rich para salida personalizada
console = Console(theme=custom_theme)


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
        """Escribe el mensaje usando Rich"""
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


def setup_logger():
    """
    Configures and sets up a logger using the Loguru library. This function initializes
    multiple log handlers including a console handler with Rich for enhanced
    visual formatting, a file handler for storing logs to a designated location,
    and an additional error-specific log file handler.

    The logger configuration includes options for log formatting, level filtering,
    log rotation, retention policies, compression, and detailed diagnostic and
    backtrace options. It ensures the log file directory exists by creating
    necessary parent directories if they do not already exist.

    :raises FileNotFoundError: If the log file path or its parent directories cannot be created.
    :raises ValueError: If any of the logger settings are invalid.
    :raises TypeError: If incorrect argument types are provided.
    :raises RuntimeError: For failures during logger handler setup.

    :return: Configured instance of the logger.
    :rtype: <type of `logger` configured>
    """

    logger.remove()

    # Handler para consola con Rich
    rich_handler = RichLogHandler(console)

    logger.add(
        rich_handler.write,
        format=format_record,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Handler para archivo
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    logger.add(
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

    # Handler para errores
    error_log_file = log_path.parent / "errors.log"

    logger.add(
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

    logger.info("✨ Logger configurado con Rich y Loguru")
    logger.debug(f"📁 Logs guardados en: {settings.LOG_FILE}")
    logger.debug(f"📊 Nivel de log: {settings.LOG_LEVEL}")

    return logger


def log_section(title: str, style: str = "bold cyan"):
    """

    """
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


# Inicializar logger
log = setup_logger()

__all__ = [
    'log',
    'console',
    'log_section',
    'log_table',
    'log_json',
    'log_panel',
    'log_tree',
    'log_status',
    'LogContext'
]