from langchain_community.document_loaders import PlaywrightURLLoader
from app.exceptions.client_error import NetworkError
from app.exceptions.server_error import URLValidationError, PageNotFoundError
from typing import List, Union
from urllib.parse import urlparse

class LoadingManagement:

    def __init__(self, 
                 url:List = None, 
                 continue_on_failure:bool = False, 
                 remove_selecore:List = ["nav",'header', 'footer', '.ads'],
                 headless:bool = True ):
        
        if self._validate_url(url):
            self.url=url
        
        self.contine=continue_on_failure
        self.remove_selectors=remove_selecore
        self.headless=headless

    async def get_documents(self):
        """load the webpage using playwright"""

        try:
            lodader = PlaywrightURLLoader(
                        urls=self.url,
                        continue_on_failure= self.contine,
                        remove_selectors= self.remove_selectors,
                        headless= self.headless)
            
            result = await lodader.aload()
            return result 
        except Exception as e:
            msg = str(e) or ""
            network_error = False
            if "net::" in msg or "ERR_NAME_NOT_RESOLVED" in msg or "ENOTFOUND" in msg:
                network_error = True
                raise NetworkError(message="NetworkError: Unable to connect ot internet.", details = {"url": self.url, "error": msg, "original_exp":e, "network_error": network_error})
            
            else:
                raise PageNotFoundError(message=f"Page not found at url {self.url}", details = {"url":self.url, "orginal_exp":e})

    
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