from typing import Optional, Union, List, Dict, Any
from app.exceptions.base import BaseException

class NetworkError(BaseException):
    def __init__(self, message: str = "Network error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status=None, code="NETWORK_ERROR", retriable=True, details=details)

class TimeoutError(BaseException):
    def __init__(self, message: str = "Request timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status=None, code="TIMEOUT", retriable=True, details=details)

class ModelNotFoundError(BaseException):
    def __init__(self, message = "Model Not found Error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status=400, code="MODEL_NOTFOUND_ERROR", retriable=True, details=details)

class PayloadTooLargeError(BaseException):
    def __init__(self, message: str = "Payload too large", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status=413, code="PAYLOAD_TOO_LARGE", details=details)