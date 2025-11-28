from typing import List
from app.exceptions.server_error import VectorStoreError, VectorStoreRetrieverError, SessionDeleteError, ValidateTextError
from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from redisvl.query.filter import Tag
from app.rag.vectorstore_manager import vectorstore_manager

from app.core.setting import setting
import logging

logger = logging.getLogger(__name__)

class StoreManagement:
    def __init__(self, docs:List[Document] = None, session_id: str = None, user_id: str = None):
        
        self.session_id = session_id
        self.user_id = user_id
        
        if not docs or len(docs) == 0:
            raise ValidateTextError(message="Data/Documents are required, shouldn't be None")
        self.splitted_docs=docs

        # Use the singleton vectorstore manager instead of creating new instances
        self.vectorstore = vectorstore_manager.vectorstore
        self.embedder = vectorstore_manager.embedder
        
        
    def store_session(self) -> VectorStore:
        """Embed docs into Redis, serialize, and save JSON to RedisVectorStore."""
        try:
            try:
                self.delete_session()
                for i, doc in enumerate(self.splitted_docs):
                    doc.metadata.update({
                        "user_id": self.user_id,
                        "session_id": self.session_id,
                        "chunk_id": i + 1,
                        "vector_id": f"{self.session_id}:chunk{i+1}"
                    })
                # Safely extract a short snippet from the first Document for debugging.
                try:
                    first_doc = self.splitted_docs[0]
                    if hasattr(first_doc, 'page_content'):
                        snippet = first_doc.page_content[:50]
                    elif hasattr(first_doc, 'content'):
                        snippet = first_doc.content[:50]
                    else:
                        snippet = str(first_doc)[:50]
                    logger.debug("Storing data into storage. snippet=%s", snippet)
                    print("Storing data into storage. snippet=%s", snippet)
                except Exception as e:
                    logger.debug("Storing data into storage. Could not extract snippet: %s", e)
                self.vectorstore.add_documents(
                    documents=self.splitted_docs,
                    ids=[doc.metadata["vector_id"] for doc in self.splitted_docs],
                )
                return self.vectorstore
            except Exception as e:
                raise VectorStoreError(message="Failed to stoer document into storage", details={'original_exp':str(e)})
        except Exception as e:
            raise VectorStoreError(
                message="Failed to store vector into storage (check API key/network/config)", details={"original_exp":str(e)}) 

    def get_retrieve_instance(self):
        """Get a retriever instance filtered by session_id and user_id"""
        try:
            # Use the manager to create a session-specific retriever
            retriever = vectorstore_manager.get_retriever(
                session_id=self.session_id,
                user_id=self.user_id,
                k=3,
                fetch_k=5,
                lambda_mult=0.5
            )
            return retriever
        except Exception as e:
            raise VectorStoreRetrieverError(message="Failed to create retriever instance", details={'original_exp':str(e)})
        
    def delete_session(self):
        """Delete specific session from vectorstorage"""
        try:
            deleted_count = self.vectorstore.delete(ids=[f"{self.session_id}:chunk{i+1}" for i in range(len(self.splitted_docs))])
            print(deleted_count)

        except Exception as e:
            raise SessionDeleteError(message=f"Failed to delete vectorstore session with session_id:{self.session_id}", details={"original_exp":str(e)})
        

    def delete_all_sessions(self, user_id: str = None):
        try:
            filter_expr = Tag("user_id") == user_id

            results = self.vectorstore.similarity_search(
                query="dummy", 
                k=10000,  
                filter=filter_expr
            )

            print(f"Found {len(results)} docs for user: {user_id}")

            ids_to_delete = [
                doc.metadata.get("vector_id")
                for doc in results
                if doc.metadata.get("vector_id") is not None
            ]
            print("IDs to delete:", ids_to_delete)

            if ids_to_delete:
                self.vectorstore.delete(ids=ids_to_delete)

        except Exception as e:
            raise SessionDeleteError(
                message=f"Failed to delete all sessions for user_id:{user_id}",
                details={"original_exp": str(e)}
            )
