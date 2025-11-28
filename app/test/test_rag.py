import unittest
from app.rag.loader import LoadingManagement
from app.rag.splitter import SplitManagement
from app.rag.vector_store import StoreManagement
from app.rag.retriever import RetrieveManagement
from app.core.setting import setting

class TestRag(unittest.TestCase):
    def setUp(self):
        self.session_id = 'test_session_123'
        self.user_id = 'test_user_123'
        self.url = ['https://www.oncampus.dev/blogs/blog-post/what-is-oncampus-complete-school-management-platform-guide']
        self.model_name = setting.embedding_model

    def test_rag_pipeline(self):
        loaded_docs = LoadingManagement(self.url).get_documents()
        self.assertTrue(loaded_docs)

        splitted_docs = SplitManagement(loaded_docs).get_split()
        self.assertTrue(splitted_docs)

        storer = StoreManagement(splitted_docs, self.session_id, self.user_id)
        storer.store_session()
        retriever_obj = storer.get_retrieve_instance()
        self.assertIsNotNone(retriever_obj)

        retriever = RetrieveManagement(
            query="who uses oncampus",
            retriever=retriever_obj,
            session_id=self.session_id,
            user_id=self.user_id
        )
        retrieved_docs = retriever.retrieve()
        self.assertTrue(retrieved_docs)
        print(retrieved_docs)

if __name__ == "__main__":
    unittest.main()