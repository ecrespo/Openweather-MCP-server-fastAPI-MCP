from decouple import config
from typing import Optional


class Settings:
    """
    Handles the application configuration settings.

    This class facilitates loading and managing configuration settings for the application,
    including server details, logging, session management, and access tokens. It ensures
    that required fields are present and offers a validation method to verify the
    integrity of the settings.

    :ivar ACCESS_KEY: The access key for the application configuration.
    :ivar URL: The base URL used for application requests.
    :ivar LOCAL_TOKEN: A local token used for authentication or access purposes.
    :ivar HOST: The hostname to bind the server.
    :ivar PORT: The port number on which the server will run.
    :ivar WORKERS: The number of worker processes for handling server requests.
    :ivar RELOAD: Indicates if the server should automatically reload on code changes.
    :ivar LOG_LEVEL: The logging level (e.g., INFO, DEBUG, ERROR).
    :ivar LOG_FILE: Path to the log file for storing logs.
    :ivar LOG_ROTATION: Specifies the log rotation size or frequency.
    :ivar LOG_RETENTION: Specifies the duration to retain log files.
    :ivar SESSION_TIMEOUT: The timeout duration (in seconds) for user sessions.
    :ivar SESSION_CLEANUP_INTERVAL: The interval (in seconds) for cleaning up expired sessions.
    """

    # Local Token Configuration
    ACCESS_KEY: str = config('ACCESS_KEY')
    URL: str = config('URL')
    LOCAL_TOKEN:str = config('LOCAL_TOKEN')
    # Server Configuration
    HOST: str = config('HOST', default='0.0.0.0')
    PORT: int = config('PORT', default=8000, cast=int)
    WORKERS: int = config('WORKERS', default=1, cast=int)
    RELOAD: bool = config('RELOAD', default=False, cast=bool)

    # Logging Configuration
    LOG_LEVEL: str = config('LOG_LEVEL', default='INFO')
    LOG_FILE: str = config('LOG_FILE', default='./logs/mcp_server.log')
    LOG_ROTATION: str = config('LOG_ROTATION', default='10 MB')
    LOG_RETENTION: str = config('LOG_RETENTION', default='7 days')

    # Session Configuration
    SESSION_TIMEOUT: int = config('SESSION_TIMEOUT', default=3600, cast=int)
    SESSION_CLEANUP_INTERVAL: int = config('SESSION_CLEANUP_INTERVAL', default=300, cast=int)

    @classmethod
    def validate(cls):
        """Valida que todas las configuraciones requeridas estén presentes"""
        required_fields = [
            'ACCESS_KEY',
            'LOCAL_TOKEN',
            'URL'
        ]

        missing = []
        for field in required_fields:
            if not getattr(cls, field, None):
                missing.append(field)

        if missing:
            raise ValueError(f"Faltan configuraciones requeridas: {', '.join(missing)}")


settings = Settings()