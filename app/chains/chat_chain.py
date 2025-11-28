from langchain_core.runnables import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_redis import vectorstores 

from app.prompts.system_prompt import PromptTemplate
from app.core.setting import setting
from app.exceptions.client_error import ModelNotFoundError
from app.database.redis_server import RedisChatMessageHistory

from .rag_chain import RAGChain
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ChatChain:
    def __init__(self,
                session_id: str = None,
                user_id: str = None,
                page_url: str = None,
                query: Optional[str] = None):
        
        self.session_id = session_id
        self.user_id = user_id
        self.page_url = page_url
        self.user_query = query


    def _get_prompt_template(self):
        template_builder = PromptTemplate()
        return template_builder.build_template()
    
    def _get_context_documents(self, query:str = None, retriever_instance:vectorstores = None):
        rag_retriever = RAGChain(self.session_id, self.user_id)
        return rag_retriever.rtrieve(query, retriever_instance)
    
    def get_session_history(self, session_id: str):
        logger.debug(f"Getting session history for session_id={session_id}, user_id={self.user_id}")
        return RedisChatMessageHistory(session_id=session_id, user_id=self.user_id)
    
    def ping_custom_model(self,
                    user_model_api_key:str = None, 
                    user_model_name:str = None,
                    user_model_max_tokens:int = None,
                    user_model_temperature:float = None):
        
        if not user_model_name or "gemini" not in user_model_name.lower():
            return {"result": False, "message": "Only Gemini models are supported (e.g., gemini-pro, gemini-1.5-pro)"}
        
        try:
            model = ChatGoogleGenerativeAI(
                model = user_model_name,
                api_key = user_model_api_key,
                temperature = user_model_temperature,
                max_output_tokens = user_model_max_tokens
            )
            # Test the model with a simple query
            result = model.invoke("Say 'test successful' if you can read this.")
            if result and hasattr(result, "content") and len(result.content) > 0:
                return {"result": True, "message": f"Successfully connected to {user_model_name}"}
            else:
                return {"result": False, "message": "Model connection failed: No response received"}
        except Exception as e:
            error_msg = str(e)
            # Hide full API key in error message
            if user_model_api_key and len(user_model_api_key) > 6:
                error_msg = error_msg.replace(user_model_api_key, f"{user_model_api_key[:6]}...")
            return {"result": False, "message": f"Model connection failed: {error_msg}"}
        
    def _config_model(self, 
                      user_model_api_key:str = None, 
                      user_model_name:str = None,
                      user_model_max_tokens:int = None,
                      user_model_temperature:float = None):
        
        try:
            return ChatGoogleGenerativeAI(
                model = user_model_name,
                api_key = user_model_api_key,
                temperature = user_model_temperature,
                max_output_tokens = user_model_max_tokens,
                convert_system_message_to_human = True
            )
        except Exception as e:
            try:
                return ChatGoogleGenerativeAI(
                    model = setting.primary_model,
                    api_key = setting.api_key,
                    temperature = setting.temperature,
                    max_output_tokens = setting.max_tokens,
                    convert_system_message_to_human = True
                )
            except Exception as e:
                try:
                    return ChatGoogleGenerativeAI(
                        model = setting.secondary_model,
                        api_key = setting.api_key,
                        temperature = setting.temperature,
                        max_output_tokens = setting.max_tokens,
                        convert_system_message_to_human = True
                    )
                except Exception as e:
                    raise ModelNotFoundError(message=f"Failed to connect to model", details={'original_exp':e})


    def run(self, query: str = None, 
            retriever_instance: vectorstores = None,
            api_key:str = None,
            model_name:str = None,
            model_temprature: float = None,
            model_max_tokens:int = None):
        
        prompt_template = self._get_prompt_template()
        
        model = self._config_model(
            user_model_api_key=api_key,
            user_model_name=model_name,
            user_model_temperature=model_temprature,
            user_model_max_tokens=model_max_tokens
        )

        context = self._get_context_documents(query, retriever_instance)

        parser = StrOutputParser()

        chain_for_runnable = prompt_template | model | parser

        # Use RunnableWithMessageHistory to auto-store messages, but don't inject history into prompt
        chain = RunnableWithMessageHistory(
            runnable=chain_for_runnable,
            get_session_history=lambda session_id: self.get_session_history(session_id),
            input_messages_key="input",
        )
        
        variables = {
            "context": context,
            "input": query,
        }

        config = {"configurable": {"session_id": self.session_id}}

        result = chain.invoke(variables, config)
        print("here is llm response", result)
        return result