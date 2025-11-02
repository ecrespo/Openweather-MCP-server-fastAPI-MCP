from typing import Optional, Dict
from utils.config import settings
from utils.logger import log


class LocalTokenValidator:
    """
    Class to validate tokens against a locally stored token.

    This class provides functionality for validating a given token by comparing it
    with a pre-defined local token. It is primarily meant to validate tokens in
    applications where a simple local token-based authentication mechanism is used.

    :ivar local_token: The token stored locally for validation purposes.
    :type local_token: str
    """

    def __init__(self):
        self.local_token = settings.LOCAL_TOKEN
        log.info("LocalTokenValidator inicializado")

    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Valida un token local comparándolo con el token almacenado

        Args:
            token: Token a validar

        Returns:
            Diccionario con información del token si es válido, None si no lo es
        """
        try:
            log.debug("Validando token local")

            if not token:
                log.warning("Token vacío")
                return None

            if token == self.local_token:
                log.info("Token validado exitosamente")
                return {
                    "valid": True,
                    "type": "local_token"
                }
            else:
                log.warning("Token inválido")
                return None

        except Exception as e:
            log.error(f"Error inesperado validando token: {e}")
            log.exception("Detalles del error:")
            return None


class LocalTokenClient:
    """
    Handles the retrieval of a locally stored token.

    This class is used to manage and provide access to a local token stored in the
    application configuration. It is useful in scenarios where authentication tokens
    are required and are stored securely within application settings.

    :ivar local_token: The local token retrieved from configuration settings for
        use in authentication or API calls.
    :type local_token: str
    """

    def __init__(self):
        self.local_token = settings.LOCAL_TOKEN
        log.info("LocalTokenClient inicializado")

    def get_token(self) -> Optional[str]:
        """
        Gets the locally stored token and returns it if available. This function logs
        the token retrieval process and handles any exceptions that occur during the
        operation. If an exception is encountered, it logs the error and returns None.

        :return: The string representation of the local token if available, or None
                 if an error occurs during retrieval.
        :rtype: Optional[str]
        """
        try:
            log.info("Obteniendo token local")
            log.debug(f"Token preview: {self.local_token[:20]}...")
            return self.local_token
        except Exception as e:
            log.error(f"Error obteniendo token local: {e}")
            log.exception("Detalles del error:")
            return None