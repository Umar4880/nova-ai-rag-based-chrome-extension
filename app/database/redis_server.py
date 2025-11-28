from typing import Optional
from redis import Redis, ConnectionPool, ConnectionError as RedisConnectionError, AuthenticationError as RedisAuthError
from datetime import datetime

from app.exceptions.database_error import DBUserNotFoundError, DBConnectionError, DBSessionNotFoundError, DBTransactionError, DBSessionDeleteError, DBSessionNotFoundError, DBTypeError
from app.core.setting import setting

from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory

import json

class RedisChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, 
                 session_id: str, 
                 user_id: str, 
                 redis_url: Optional[str] = None, 
                 ttl_seconds: Optional[int] = 86400):  # 24 hours default TTL
        if not user_id:
            raise DBUserNotFoundError(message="User id is required (User id shouldn't be None)")
        self.user_id = user_id

        if not session_id:
            raise DBSessionNotFoundError(message="Session id is required (Session id shouldn't be None)") # Specific error for session ID
        self.session_id = session_id
       
        if not redis_url:
           self.redis_url = setting.redis_db_url
        else:
           self.redis_url = redis_url

        self.ttl_timeout = ttl_seconds
        self.chat_key = f"session:{self.user_id}:{self.session_id}:chat"

        self._pool= self._get_redis_connection_pool()
        self._client= self._get_client()

    def _get_redis_connection_pool(self) -> ConnectionPool:
        """Manages connection pooling for efficiency."""
        try:
            self._pool = ConnectionPool.from_url(
                url=self.redis_url, 
                decode_responses=True
            )
        except Exception as e:
            raise DBConnectionError(message="Unable to create Redis connection pool", details={"original_exp":e})
        return self._pool
    
    def _get_client(self) -> Redis:
        """Gets a client from the connection pool."""
        pool = self._pool
        client = Redis(connection_pool=pool)
        
        try:
            client.ping()
        except (RedisConnectionError, RedisAuthError) as e:
             raise DBConnectionError(message="Redis server did not respond or authentication failed", details={"original_exp":e})

        return client
    
    def create_session(self):
        try:
            # If the session chat key already exists, do nothing (preserve existing history)
            if not self._client.exists(self.chat_key):
                # Create a small metadata hash for the session (registers the session)
                meta_key = f"session:{self.user_id}:{self.session_id}:meta"
                self._client.hset(
                    meta_key,
                    mapping={
                        "user_id": self.user_id,
                        "session_id": self.session_id,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                )
                # Ensure TTL is set for both chat history key and meta key
                if self.ttl_timeout:
                    self._client.expire(self.chat_key, self.ttl_timeout)
                    self._client.expire(meta_key, self.ttl_timeout)
            return True
        except DBTypeError as e:
            raise e
        except Exception as e:
            raise DBTransactionError(message="unable to create session", details={"original_exp": e})

    @property
    def messages(self):
        try:
            existing_messages = self._client.lrange(self.chat_key, 0, -1)
            deserilaized_messages = [json.loads(msg) for msg in existing_messages]
            
            # Refresh TTL when accessing messages to keep session alive
            if self.ttl_timeout and existing_messages:
                self._client.expire(self.chat_key, self.ttl_timeout)
            
            return messages_from_dict(deserilaized_messages)
        except Exception as e:
            raise DBSessionNotFoundError(message=f"Failed to load all messages for chat_key:{self.chat_key}", details={'original_exp':e})
        
    def add_messages(self, message: BaseMessage):
        try:
            # Accept either a single message, a list of messages, or already-serialized dicts
            if isinstance(message, list):
                for m in message:
                    if isinstance(m, dict):
                        serialized = m
                    else:
                        serialized = message_to_dict(m)
                    self._client.rpush(self.chat_key, json.dumps(serialized))
            else:
                if isinstance(message, dict):
                    serialized_message = message
                else:
                    serialized_message = message_to_dict(message)
                self._client.rpush(self.chat_key, json.dumps(serialized_message))
            
            # Refresh TTL on every message to keep session alive
            if self.ttl_timeout:
                self._client.expire(self.chat_key, self.ttl_timeout)
        except Exception as e:
            raise DBTransactionError(message=f"Failed to store message in sessino:{self.session_id}", details={'original_exp':e})
        
    def clear(self):
        try:
            self._client.delete(self.chat_key)
        except BaseException as e:
            raise DBSessionDeleteError(message=f"Failed to delete session with id:{self.session_id} for user:{self.user_id}", details={'original_exp':e})
        
    def get_all_session_names(self):
        pattern = f"session:{self.user_id}:*:chat"
        return self._client.keys(pattern)