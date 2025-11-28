from .base import BaseException
from typing import Optional, Dict, Union, List, Any

class InternalSeverError(BaseException):
    def __init__(self, message = "Internal Sever Error",  details=None):
        super().__init__(message=message, status=500, code="INTERNAL_SERVER_ERROR", details=details)

class ExternalSeverError(BaseException):
    def __init__(self, message = "External Sever Error",  details=None):
        super().__init__(message=message, status=503, code="EXTERNAL_SERVER_ERROR", details=details)

class ConfigurationError(BaseException):
    def __init__(self, message = "Configuration Error",  details=None):
        super().__init__(message=message, status=503, code="CONFIGURATION_ERROR", details=details)

class TypeValidationError(BaseException):
    def __init__(self, message = "Type Error",  details=None):
        super().__init__(message=message, status=500, code="TYPE_ERROR", details=details)

#-------------------------------RAG----------------------------#
class URLValidationError(BaseException):
    def __init__(self, message: str = "Invalid URL", url: Optional[Union[str, List[str]]] = None, details = None):
        d = dict(details or {})
        if url is not None:
            d.setdefault("url", url)
        super().__init__(message, status=400, code="INVALID_URL", details=d)

class PageNotFoundError(BaseException):
     def __init__(self, message: str = "Unable to load page", url: Optional[Union[str, List[str]]] = None, details: Optional[Dict[str, Any]] = None):
        d = dict(details or {})
        if url is not None:
            d.setdefault("url", url)
        super().__init__(message, status=404, code="PAGE_NOTFOUND_ERROR", details=details)

class ValidateTextError(BaseException):
    def __init__(self, message = "Invalid Text", details=None):
        super().__init__(message=message, status=400, code="INVALID_TEXT", details=details)

class PromptValidationError(BaseException):
    def __init__(self, message = "Prompt Validation Error",  details=None):
        super().__init__(message=message, status=500, code="PROMPT_VALIDATION_ERROR", details=details)

class ObjectNotFoundError(BaseException):
    def __init__(self, message = "Object Not Found Error",  details=None):
        super().__init__(message=message, status=500, code="OBJECT_NOTFOUND_ERROR", details=details)

class VectorStoreError(BaseException):
    def __init__(self, message = "Vector Store Error",  details=None):
        super().__init__(message=message, status=500, code="VECTOR_STORE_ERROR", details=details)

class VectorStoreRetrieverError(BaseException):
    def __init__(self, message = "Vectorstore retriever Error",  details=None):
        super().__init__(message=message, status=500, code="VECTOR_RETRIEVER_ERROR", details=details)

class VectorDeSerialzeError(BaseException):
    def __init__(self, message = "Vector deserialze Error",  details=None):
        super().__init__(message=message, status=500, code="VECTOR_DESERIALZE_ERROR", details=details)

class RetrieverError(BaseException):
    def __init__(self, message = "Retriever Error",  details=None):
        super().__init__(message=message, status=500, code="RETRIEVER_ERROR", details=details)

class SessionDeleteError(BaseException):
    def __init__(self, message = "Unable to delete Vectoer Session",  details=None):
        super().__init__(message=message, status=500, code="SESSION_DELETE_ERROR", details=details)