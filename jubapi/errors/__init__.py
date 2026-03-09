from typing import Any, Dict
from fastapi import HTTPException

class JubError(Exception):
    """
    Base exception class for the Jub API.

    Attributes:
        status_code (int): The HTTP status code associated with the error.
        detail (Any): Additional details or message regarding the error.
        metadata (Dict[str, str]): Optional headers or metadata to include in the response.
    """
    def __init__(self, status_code: int, detail: Any = None, metadata: Dict[str, str]  = None) -> None:
        """
        Initializes the base JubError.

        Args:
            status_code (int): The HTTP status code to return.
            detail (Any, optional): The error message or details. Defaults to None.
            metadata (Dict[str, str], optional): Additional HTTP headers. Defaults to None.
        """
        self.status_code = status_code
        self.detail = detail
        self.metadata = metadata
        # super().__init__(status_code, detail, headers)
    
    @staticmethod
    def from_exception(exc: Exception) -> 'JubError':
        
        """
        Converts any exception into a JubError with a 500 status code.
        
        Args:
            exc (Exception): The original exception caught by the application.

        Returns:
            JubError: A new instance of JubError wrapping the original exception.
        """
        return JubError(status_code=500, detail=str(exc))

    @staticmethod
    def to_http_exception(jub_error: 'JubError') -> HTTPException:
        """
        Converts a JubError into a FastAPI HTTPException.
        
        Args:
            jub_error (JubError): The JubError instance to convert.

        Returns:
            HTTPException: The corresponding FastAPI HTTP exception.
        """
        return HTTPException(status_code=jub_error.status_code, detail=jub_error.detail, headers=jub_error.metadata)

class UnknownError(JubError):
    """Represents an unknown or internal server error (HTTP 500)."""
    def __init__(self,detail: Any = None, headers: Dict[str, str]  = None) -> None:
        """
        Initializes the UnknownError.

        Args:
            detail (Any, optional): The error message or details. Defaults to None.
            headers (Dict[str, str], optional): Additional HTTP headers. Defaults to None.
        """
        super().__init__(500, detail, headers)

class NotFound(JubError):
    """Represents a resource not found error (HTTP 404)."""
    def __init__(self,detail: Any = None, headers: Dict[str, str]  = None) -> None:
        """
        Initializes the NotFound error.

        Args:
            detail (Any, optional): The error message or details. Defaults to None.
            headers (Dict[str, str], optional): Additional HTTP headers. Defaults to None.
        """
        super().__init__(404, detail, headers)

class CreationError(JubError):
    """Represents an error that occurs during resource creation (HTTP 400)."""
    def __init__(self,detail: Any = None, headers: Dict[str, str]  = None) -> None:
        """
        Initializes the CreationError.

        Args:
            detail (Any, optional): The error message or details. Defaults to None.
            headers (Dict[str, str], optional): Additional HTTP headers. Defaults to None.
        """
        super().__init__(400, detail, headers)
        

class AlreadyExists(JubError):
    """Represents a conflict error where a resource already exists (HTTP 403)."""
    def __init__(self,detail: Any = None, headers: Dict[str, str] = None) -> None:
        """
        Initializes the AlreadyExists error.

        Args:
            detail (Any, optional): The error message or details. Defaults to None.
            headers (Dict[str, str], optional): Additional HTTP headers. Defaults to None.
        """
        super().__init__(403, detail, headers)