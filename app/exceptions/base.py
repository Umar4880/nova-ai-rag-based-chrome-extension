from typing import Any, Dict, Optional
import logging
import os
import sys
from logging import FileHandler, Formatter, StreamHandler

# Ensure the log directory exists under the package `app/log` (absolute path)
pkg_dir = os.path.dirname(os.path.dirname(__file__))  # points to .../app
log_dir = os.path.join(pkg_dir, 'log')
os.makedirs(log_dir, exist_ok=True)

# Use absolute logfile path
logfile = os.path.join(log_dir, 'app.log')

# Configure root logger with a FileHandler to avoid being overridden by uvicorn
root_logger = logging.getLogger()

# Allow runtime control of log level via environment variable APP_LOG_LEVEL (DEBUG/INFO/WARNING/ERROR)
level_name = os.getenv('APP_LOG_LEVEL', 'ERROR').upper()
log_level = getattr(logging, level_name, logging.ERROR)
root_logger.setLevel(log_level)

# Add a FileHandler if not already present for the same logfile
existing_file_handlers = [h for h in root_logger.handlers if isinstance(h, FileHandler) and getattr(h, 'baseFilename', None) == os.path.abspath(logfile)]
if not existing_file_handlers:
    fh = FileHandler(logfile)
    fh.setLevel(log_level)
    fh.setFormatter(Formatter('%(asctime)s %(levelname)s %(message)s'))
    root_logger.addHandler(fh)

# Add a console StreamHandler for local debugging or when explicitly requested.
# Console logging can be enabled by setting one of the following environment variables:
# - APP_ENV=local|development
# - APP_LOG_TO_STDOUT=1 (or 'true')
# Also automatically enable console logging when log level is DEBUG.
env = os.getenv('APP_ENV', '').lower()
log_to_stdout = os.getenv('APP_LOG_TO_STDOUT', '').lower() in ('1', 'true', 'yes')
add_console = env in ('local', 'development', 'dev') or log_to_stdout or (log_level == logging.DEBUG)
if add_console:
    existing_stream_handlers = [h for h in root_logger.handlers if isinstance(h, StreamHandler) and getattr(h, 'stream', None) is sys.stdout]
    if not existing_stream_handlers:
        sh = StreamHandler(stream=sys.stdout)
        sh.setLevel(log_level)
        sh.setFormatter(Formatter('%(asctime)s %(levelname)s %(message)s'))
        root_logger.addHandler(sh)

class BaseException(Exception):
    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        code: Optional[str] = None,
        retriable: bool = False,
        original: Optional[BaseException] = None,
        details: Optional[Dict[str, Any]] = None,
        log: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.retriable = retriable
        self.original = original
        self.details = details or {}

        if log:
            logging.error(f"[{self.code}] {self.message} | Details: {self.details}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "status": self.status,
            "code": self.code,
            "retriable": self.retriable,
            "details": self.details,
        }
    
    def is_retriable(err: BaseException) -> bool:
        return err.retriable