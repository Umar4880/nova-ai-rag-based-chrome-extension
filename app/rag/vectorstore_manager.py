"""
Enterprise Vectorstore Manager - Singleton Pattern
Creates a single shared vectorstore connection for the entire application
"""
from typing import Optional
from langchain_redis import RedisVectorStore
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from redis import Redis
from redisvl.query.filter import Tag
from app.core.setting import setting
from app.exceptions.client_error import ModelNotFoundError
from app.exceptions.server_error import VectorStoreError, VectorStoreRetrieverError
import logging

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Singleton manager for global vectorstore instance"""
    
    _instance: Optional['VectorStoreManager'] = None
    _vectorstore: Optional[RedisVectorStore] = None
    _embedder: Optional[GoogleGenerativeAIEmbeddings] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if self._vectorstore is None:
            self._initialize_vectorstore()
    
    def _initialize_vectorstore(self, api_key: str = None):
        """Initialize the global vectorstore connection (called only once)"""
        if not api_key:
            model_api_key = setting.api_key
        else:
            model_api_key = api_key
        try:
            self._embedder = GoogleGenerativeAIEmbeddings(
                model=setting.embedding_model,
                google_api_key=model_api_key
            )
        except Exception as e:
            raise ModelNotFoundError(
                message=f"Failed to connect to embedding model {setting.embedding_model}",
                details={
                    "model_name": setting.embedding_model,
                    "api_key": setting.api_key,
                    "original_exp": str(e)
                }
            )
        
        try:
            metadata_schema = [
                {"name": "user_id", "type": "tag"},
                {"name": "session_id", "type": "tag"},
            ]
            
            self._vectorstore = RedisVectorStore(
                embeddings=self._embedder,
                index_name="global_index",
                redis_client=Redis.from_url(setting.redis_vector_url),
                metadata_schema=metadata_schema
            )
        except Exception as e:
            raise VectorStoreError(
                message="Failed to create global vectorstore instance",
                details={'original_exp': str(e)}
            )
    
    def get_vectorstore(self, api_key: str = None) -> RedisVectorStore:
        """Get the shared vectorstore instance"""
        if self._vectorstore is None:
            self._initialize_vectorstore(api_key=api_key)
        return self._vectorstore
    
    @property
    def vectorstore(self) -> RedisVectorStore:
        """Get the shared vectorstore instance (backward compatibility)"""
        return self.get_vectorstore()
    
    def get_embedder(self, api_key: str = None) -> GoogleGenerativeAIEmbeddings:
        """Get the shared embedder instance"""
        if self._embedder is None:
            self._initialize_vectorstore(api_key=api_key)
        return self._embedder
    
    @property
    def embedder(self) -> GoogleGenerativeAIEmbeddings:
        """Get the shared embedder instance (backward compatibility)"""
        return self.get_embedder()
    
    def get_retriever(self, session_id: str, user_id: Optional[str] = None, api_key: str = None, **search_kwargs):
        """
        Create a retriever filtered by session_id and optionally user_id
        
        Args:
            session_id: The session identifier
            user_id: Optional user identifier for additional filtering
            api_key: Optional user-provided API key for embeddings
            **search_kwargs: Additional search parameters (k, fetch_k, lambda_mult, etc.)
        
        Returns:
            A retriever instance filtered for the specific session
        """
        try:
            # Ensure vectorstore is initialized with correct API key
            vectorstore = self.get_vectorstore(api_key=api_key)
            
            # Build filter expression
            filter_expr = Tag("session_id") == session_id
            if user_id:
                filter_expr = filter_expr & (Tag("user_id") == user_id)
            
            logger.debug(f"Creating retriever with filter: session_id={session_id}, user_id={user_id}")
            logger.debug(f"Filter expression: {filter_expr}")
            
            # Default search kwargs (WITHOUT filter - filter goes to as_retriever directly)
            default_kwargs = {
                "k": 3,
                "fetch_k": 5,
                "lambda_mult": 0.5
            }
            default_kwargs.update(search_kwargs)
            
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs=default_kwargs,
                filter=filter_expr  # Pass filter here, not inside search_kwargs
            )
            return retriever
        except Exception as e:
            raise VectorStoreRetrieverError(
                message="Failed to create retriever instance",
                details={'session_id': session_id, 'user_id': user_id, 'original_exp': str(e)}
            )

# Global instance
vectorstore_manager = VectorStoreManager()