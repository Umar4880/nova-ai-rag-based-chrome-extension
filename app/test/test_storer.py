from app.rag.vector_store import StoreManagement
from langchain_core.documents import Document

def test_store_and_retrieve():
    # Create dummy docs for testing
    docs = [
        Document(page_content="Test chunk one"),
        Document(page_content="Test chunk two"),
    ]
    session_id = "test-session"
    user_id = "test-user"

    # Instantiate storer
    storer = StoreManagement(docs=docs, session_id=session_id, user_id=user_id)
    try:
        print("Storing documents...")
        vector_store = storer.store_session()
        print("Stored vector store:", vector_store)
    except Exception as e:
        print("Error during storing:", e)
        
        return

    print("Retrieving retriever instance...")
    try:
        retriever = storer.get_retrieve_instance()
        print("Retriever object:", retriever)
        # Try a simple query
        results = retriever.invoke("test two")
        print("Retrieved docs:", results)
    except Exception as e:
        print("Error during retrieval:", e)

if __name__ == "__main__":
    test_store_and_retrieve()