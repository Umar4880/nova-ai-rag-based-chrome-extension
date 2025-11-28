from typing import List
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from app.exceptions.server_error import ValidateTextError, TypeValidationError, RetrieverError
import logging

logger = logging.getLogger(__name__)

class RetrieveManagement:
    def __init__(self, 
                 query: str, 
                 retriever: BaseRetriever = None,
                 session_id:str = None,
                 user_id: str = None):
        
        if not query:
            raise ValidateTextError(message="Query is required (shouldn't be None)")
        self.user_query = query
        
        if not retriever:
            raise TypeValidationError(message="A valid retriever instance must be provided.")
        self.retriever = retriever
        
        self.session_id=session_id
        self.user_id=user_id
        self.results: List[Document] = self.retrieve()
        
    def retrieve(self) -> List[Document]:
        """Internal method to invoke the retriever with the user query."""
        logger.debug(f"Retrieving documents for query: '{self.user_query}' (session={self.session_id}, user={self.user_id})")
        try:
            documents = self.retriever.invoke(self.user_query)
            logger.debug(f"Retrieved {len(documents)} documents")
            if documents:
                for i, doc in enumerate(documents[:2]):  # Log first 2 docs
                    snippet = doc.page_content[:100] if hasattr(doc, 'page_content') else str(doc)[:100]
                    logger.debug(f"  Doc {i+1} snippet: {snippet}")
            else:
                logger.warning(f"No documents retrieved for query '{self.user_query}' in session {self.session_id}")
            return documents
        except Exception as e:
            raise RetrieverError(message="RetrieverError: Unable to retrieve document", details={"original_exp":e})
        
    def get_results(self) -> List[Document]:
        """Public method to get the retrieved documents."""
        return self.results
