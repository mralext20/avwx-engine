"""
Service base class
"""

# pylint: disable=too-few-public-methods

# stdlib
from socket import gaierror
from typing import Any, Tuple

# library
import httpx
import httpcore

# module
from avwx.exceptions import SourceError

_VALUE_ERROR = "'{}' is not a valid report type for {}. Expected {}"


class Service:
    """Base Service class for fetching reports"""

    url: str = None
    report_type: str
    _valid_types: Tuple[str] = tuple()

    def __init__(self, report_type: str):
        if self._valid_types:
            if report_type not in self._valid_types:
                raise ValueError(
                    _VALUE_ERROR.format(
                        report_type, self.__class__.__name__, self._valid_types
                    )
                )
        self.report_type = report_type

    def fetch(self, station: str, timeout: int = 10) -> str:
        """Fetches a report string from the service"""
        raise NotImplementedError()

    async def async_fetch(self, station: str, timeout: int = 10) -> str:
        """Asynchronously fetch a report string from the service"""
        raise NotImplementedError()


class CallsHTTP:
    """Service supporting HTTP requests"""

    method: str = "GET"

    async def _call(
        self,
        url: str,
        params: dict = None,
        headers: dict = None,
        data: Any = None,
        timeout: int = 10,
    ) -> str:
        name = self.__class__.__name__
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if self.method.lower() == "post":
                    resp = await client.post(
                        url, params=params, headers=headers, data=data
                    )
                else:
                    resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    raise SourceError(f"{name} server returned {resp.status_code}")
        except (
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpcore.ReadTimeout,
        ) as timeout_error:
            raise TimeoutError(f"Timeout from {name} server") from timeout_error
        except (gaierror, httpcore.ConnectError, httpx.ConnectError) as connect_error:
            raise ConnectionError(
                f"Unable to connect to {name} server"
            ) from connect_error
        except httpcore.NetworkError as network_error:
            raise ConnectionError(
                f"Unable to read data from {name} server"
            ) from network_error
        return resp.text
