from app.rag.loader import LoadingManagement
from app.rag.splitter import SplitManagement
from app.rag.vector_store import StoreManagement
from app.rag.retriever import RetrieveManagement
from app.exceptions.server_error import ValidateTextError

from langchain_redis import vectorstores

class RAGChain:
    def __init__(self,
                session_id: str = None,
                user_id: str = None,):
          
        self.session_id = session_id
        self.user_id = user_id

    async def store(self, page_url: str = None):
        loader = LoadingManagement(url = [page_url])
        self.loaded_docs = await loader.get_documents()

        splitter = SplitManagement(self.loaded_docs)
        self.splited_docs = splitter.get_split()

        storer = StoreManagement(self.splited_docs, self.session_id, self.user_id)
        storer.store_session()
        
        return storer.get_retrieve_instance()

    def rtrieve(self, query:str = None, retriever_instance:vectorstores = None ):
        if not query or len(query) == 0:
            raise ValidateTextError(message=f"Invalid user query(user query must not be None) user_query:{query}")
        user_query = query

        retriever = RetrieveManagement(
                            user_query,
                            retriever_instance,
                            self.session_id,
                            self.user_id)
        
        return retriever.retrieve()