from app.chains.chat_chain import ChatChain
from app.chains.rag_chain import RAGChain
from app.database.redis_server import RedisChatMessageHistory

from langchain_core.messages import messages_to_dict
from langchain_redis import vectorstores
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self,
                 session_id: str = None,
                 user_id: str = None):
        
        self.session_id = session_id
        self.user_id = user_id

        self.retriever_instance = None
        self.chat_chian_instance = ChatChain(self.session_id, self.user_id)
        self.rag_chain_instance = RAGChain(self.session_id, self.user_id, )
        self.redis_db_instance = RedisChatMessageHistory(self.session_id, self.user_id)

    async def start_session(self, page_url: str = None):
        self.redis_db_instance.create_session()
        return await self.rag_chain_instance.store(page_url)
    
    def ping_custom_model(self,
                     api_key: str = None,
                     model_name: str = None,
                     model_temperature: float = None,
                     model_max_tokens: int = None):
        
        result = self.chat_chian_instance.ping_custom_model(
            user_model_api_key=api_key,
            user_model_name=model_name,
            user_model_temperature=model_temperature,
            user_model_max_tokens=model_max_tokens
        )
        
        return result

    def send_message(self, 
                     query: str = None, 
                     retriever_instance: vectorstores = None,
                     api_key: str = None,
                     model_name: str = None,
                     model_temperature: float = None,
                     model_max_tokens: int = None):
        
        logger.debug(f"Processing message for session {self.session_id}, user {self.user_id}")
        
        result = self.chat_chian_instance.run(
            query=query,
            retriever_instance=retriever_instance,
            api_key=api_key,
            model_name=model_name,
            model_temprature=model_temperature,
            model_max_tokens=model_max_tokens
        )
        
        logger.debug(f"Message processed successfully for session {self.session_id}")
        return result
    
    def get_chat_history(self):
        messages = self.redis_db_instance.messages
        return messages_to_dict(messages)
    
    def delete_session(self):
        self.redis_db_instance.clear()

    