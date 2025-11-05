"""
Authentication Protocols for Token Validation and Provisioning.

This module defines protocol interfaces for token validation and token provision,
allowing different authentication mechanisms to be used interchangeably while
maintaining type safety and a consistent interface.
"""

from typing import Protocol, Optional, Dict


class TokenValidator(Protocol):
    """
    Protocol for token validation implementations.

    This protocol defines the interface that all token validators must implement.
    It enables different validation strategies (local tokens, JWT, OAuth2, etc.)
    to be used interchangeably throughout the application.

    Example implementations:
        - LocalTokenValidator: Validates against a stored local token
        - JWTValidator: Validates JSON Web Tokens
        - OAuth2Validator: Validates OAuth2 access tokens
    """

    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validates a token and returns token information if valid.

        Args:
            token: The token string to validate

        Returns:
            A dictionary containing token information if valid, including:
                - valid: bool indicating if the token is valid
                - type: str indicating the token type (e.g., 'local_token', 'jwt')
                - Additional token-specific metadata
            Returns None if the token is invalid

        Raises:
            Exception: May raise exceptions for unexpected errors during validation
        """
        ...


class TokenProvider(Protocol):
    """
    Protocol for token provisioning implementations.

    This protocol defines the interface for components that provide or retrieve
    authentication tokens. It enables different token sources to be used
    interchangeably.

    Example implementations:
        - LocalTokenClient: Retrieves a locally stored token
        - JWTTokenGenerator: Generates JWT tokens
        - OAuth2TokenClient: Retrieves OAuth2 tokens from an auth server
        - CachedTokenProvider: Provides tokens from a cache
    """

    def get_token(self) -> Optional[str]:
        """
        Retrieves or generates an authentication token.

        Returns:
            The token string if available, None if unable to retrieve/generate

        Raises:
            Exception: May raise exceptions for unexpected errors during retrieval
        """
        ...