import asyncio
import logging
from typing import List, Union
from urllib.parse import urlparse

from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_core.documents import Document
from app.exceptions.client_error import NetworkError
from app.exceptions.server_error import URLValidationError, PageNotFoundError

logger = logging.getLogger(__name__)

class LoadingManagement:

    def __init__(self, 
                 url: List = None, 
                 continue_on_failure: bool = True, 
                 remove_selecore: List = ["nav", "header", "footer", ".ads"],
                 headless: bool = True):
        
        if self._validate_url(url):
            self.url = url
        
        self.contine = continue_on_failure
        self.remove_selectors = remove_selecore
        self.headless = headless

    async def get_documents(self):
        """load the webpage using playwright"""
        try:
            loader = PlaywrightURLLoader(
                urls=self.url,
                continue_on_failure=self.contine,
                remove_selectors=self.remove_selectors,
                headless=self.headless,
            )
            
            # Run synchronous loader in worker thread to prevent Windows
            # asyncio SelectorEventLoop NotImplementedError with subprocesses
            result = await asyncio.to_thread(loader.load)

            # If page loaded without text content (or auth wall / empty SPA),
            # provide a fallback document so RAG chain doesn't break
            if not result or not any(doc.page_content.strip() for doc in result):
                main_url = self.url[0] if isinstance(self.url, list) and self.url else str(self.url)
                return [
                    Document(
                        page_content=f"Current Webpage: {main_url}\nNote: Dynamic content could not be rendered from this page. You can still ask questions about this page or general questions.",
                        metadata={"source": main_url}
                    )
                ]

            return result 
        except Exception as e:
            msg = str(e) or ""
            if "net::" in msg or "ERR_NAME_NOT_RESOLVED" in msg or "ENOTFOUND" in msg:
                raise NetworkError(message="NetworkError: Unable to connect to internet.", details={"url": self.url, "error": msg, "original_exp": e, "network_error": True})
            
            # If Playwright fails on a specific complex/protected URL,
            # return a fallback document rather than failing the entire chat session creation
            logger.warning(f"Could not load webpage {self.url} with Playwright: {e}. Using fallback document.")
            main_url = self.url[0] if isinstance(self.url, list) and self.url else str(self.url)
            return [
                Document(
                    page_content=f"Current Webpage: {main_url}\nNote: Page content could not be extracted directly. You can still ask questions about this page or general questions.",
                    metadata={"source": main_url}
                )
            ]

    
    def _validate_url(self, url: List = None) -> bool:
        """Validate a single URL string or a list of URL strings."""
        if not url:
            raise URLValidationError(message="URL is required", url=url)

        if isinstance(url, (list, tuple)):
            if len(url) == 0:
                raise URLValidationError(message="URL list must contain at least one URL", url=url)
            for u in url:
                if not isinstance(u, str):
                    raise URLValidationError(message="Each URL must be a string", url=u)
                parsed = urlparse(u)
                if parsed.scheme.lower() not in ("http", "https"):
                    raise URLValidationError(message="Invalid URL (must be http or https)", url=u)
            return True