from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Union
from langchain_core.documents import Document
from app.exceptions.server_error import ValidateTextError

class SplitManagement:
    def __init__(self, docs:Union[List[Document] | str] = None, chunk_size:int = 1000, chunk_overlap:int =200):
        if not docs:
            raise ValidateTextError(message="Text required (Text must be provide)", details={'text': docs})
        
        self.docs=docs
        self.chunk_size=chunk_size
        self.chunk_overlap=chunk_overlap
        
    def get_split(self) -> List[Document]:
        try:
            splitter = RecursiveCharacterTextSplitter(["\n\n", "\n", " ", ""], self.chunk_size, self.chunk_overlap)

            if isinstance(self.docs, str):
                splitted_text = splitter.split_text(self.docs)
                return [Document(page_content=text) for text in splitted_text]
            
            if not isinstance(self.docs, List):
                raise ValidateTextError(message="Data must be a List of Documents or String")
            for i, item in enumerate(self.docs):
                if not isinstance(item, Document):
                    raise ValidateTextError(message="All items in docs must be Document", details={"bad_index": i, "bad_value": repr(item)})
                
            splitted_text = splitter.split_documents(self.docs)
            return splitted_text
        except Exception as e:
            raise ValidateTextError(message="Unable to split text/docs", details={"original_exp":e})