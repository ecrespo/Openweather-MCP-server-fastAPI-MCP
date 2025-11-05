"""
HTTP Client Service.

This module provides a centralized HTTP client service for making API calls.
It wraps httpx functionality and provides consistent configuration across the application.
"""

from typing import Any, Dict, Optional
import httpx
from utils.logger import log


class HTTPClient:
    """
    HTTP Client service for making API calls.

    This class provides a centralized way to make HTTP requests with
    consistent configuration (timeout, headers, etc.) and better testability.

    :ivar timeout: Default timeout for HTTP requests in seconds
    :ivar default_headers: Default headers to include in all requests
    """

    def __init__(
        self,
        timeout: float = 10.0,
        default_headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the HTTP client.

        Args:
            timeout: Default timeout for requests in seconds
            default_headers: Optional default headers to include in all requests
        """
        self.timeout = timeout
        self.default_headers = default_headers or {}
        log.debug(f"HTTPClient initialized with timeout={timeout}s")

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Make a GET request.

        Args:
            url: The URL to request
            params: Optional query parameters
            headers: Optional headers (merged with default headers)
            timeout: Optional timeout override

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        merged_headers = {**self.default_headers, **(headers or {})}
        request_timeout = timeout or self.timeout

        log.debug(f"GET {url} with params={params}")

        try:
            response = httpx.get(
                url,
                params=params,
                headers=merged_headers,
                timeout=request_timeout
            )
            log.debug(f"GET {url} returned status {response.status_code}")
            return response
        except httpx.HTTPError as e:
            log.error(f"HTTP error during GET {url}: {e}")
            raise

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Make a POST request.

        Args:
            url: The URL to request
            data: Optional form data
            json: Optional JSON body
            headers: Optional headers (merged with default headers)
            timeout: Optional timeout override

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        merged_headers = {**self.default_headers, **(headers or {})}
        request_timeout = timeout or self.timeout

        log.debug(f"POST {url}")

        try:
            response = httpx.post(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                timeout=request_timeout
            )
            log.debug(f"POST {url} returned status {response.status_code}")
            return response
        except httpx.HTTPError as e:
            log.error(f"HTTP error during POST {url}: {e}")
            raise

    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Make a PUT request.

        Args:
            url: The URL to request
            data: Optional form data
            json: Optional JSON body
            headers: Optional headers (merged with default headers)
            timeout: Optional timeout override

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        merged_headers = {**self.default_headers, **(headers or {})}
        request_timeout = timeout or self.timeout

        log.debug(f"PUT {url}")

        try:
            response = httpx.put(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                timeout=request_timeout
            )
            log.debug(f"PUT {url} returned status {response.status_code}")
            return response
        except httpx.HTTPError as e:
            log.error(f"HTTP error during PUT {url}: {e}")
            raise

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Make a DELETE request.

        Args:
            url: The URL to request
            headers: Optional headers (merged with default headers)
            timeout: Optional timeout override

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        merged_headers = {**self.default_headers, **(headers or {})}
        request_timeout = timeout or self.timeout

        log.debug(f"DELETE {url}")

        try:
            response = httpx.delete(
                url,
                headers=merged_headers,
                timeout=request_timeout
            )
            log.debug(f"DELETE {url} returned status {response.status_code}")
            return response
        except httpx.HTTPError as e:
            log.error(f"HTTP error during DELETE {url}: {e}")
            raise