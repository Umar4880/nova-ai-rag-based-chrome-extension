from .base import BaseException
from typing import List

class DBConnectionError(BaseException):
    def __init__(self, message = "Unable to initalize database",  details=None):
        super().__init__( message, status=503, code="DB_INIT_ERROR", details=details)

class DBTransactionError(BaseException):
    def __init__(self, message = "Transaction failed",  details=None):
        super().__init__( message, status=503, code="TRANSACTION_ERROR", details=details)

class DBNotFoundError(BaseException):
    def __init__(self, message = "database not found",  details=None):
        super().__init__( message, status=404, code="DB_NOTFOUND_ERROR", details=details)

class DBMigrationError(BaseException):
    def __init__(self, message = "Unable to migrate to database",  details=None):
        super().__init__( message, status=503, code="DB_MIGARTION_ERROR", details=details)

class DBUserNotFoundError(BaseException):
    def __init__(self, message = "Invalid User id",  details=None):
        super().__init__( message, status=503, code="DB_User_NOTFOUND_ERROR", details=details)

class DBSessionNotFoundError(BaseException):
    def __init__(self, message = "Invalid Session id",  details=None):
        super().__init__( message, status=503, code="DB_Session_NOTFOUND_ERROR", details=details)

class DBURLError(BaseException):
    def __init__(self, message = "Invalid database url",  details=None):
        super().__init__( message, status=500, code="DB_URL_ERROR",  details=details)

class DBTypeError(BaseException):
    def __init__(self, message = "Invalid datatype of data",  details=None):
        super().__init__( message, status=500, code="DB_TYPE_ERROR",  details=details)

class DBExpireError(BaseException):
    def __init__(self, message = "Unable to expire session connectiom",  details=None):
        super().__init__( message, status=500, code="DB_EXPIRE_ERROR",  details=details)

class DBSessionDeleteError(BaseException):
    def __init__(self, message = "Unable to delete chat Session",  details=None):
        super().__init__(message=message, status=500, code="DB_SESSION_DELETE_ERROR", details=details)