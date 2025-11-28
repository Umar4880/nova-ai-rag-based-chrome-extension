from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from ..utils.ids import generate_session_id, generate_user_id
from app.services.chat_service import ChatService
from app.rag.vectorstore_manager import vectorstore_manager

router = APIRouter(prefix="/api/v1")

class Request(BaseModel):
    session_id: str = Field(..., description="session id")
    user_id: str = Field(..., description="user id")

class PingRequest(BaseModel):
    api_key: str = Field(..., description="api key for model")
    model_name: str = Field(..., description="name of model")
    model_temperature: float = Field(..., description="temperature for model")
    model_max_tokens: int = Field(..., description="max tokens for model")

class SessionRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    page_url: str

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    message: str = "Session created successfully"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="user message")
    session_id: str = Field(..., description="session id")
    user_id: Optional[str] = None
    # Custom LLM settings (optional)
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    model_temperature: Optional[float] = None
    model_max_tokens: Optional[int] = None

class HistoryResponse(BaseModel):
    messages:list
    session_id:str
    user_id:str

@router.post("/session/new", response_model=SessionResponse)
async def create_session(request: SessionRequest):

    session_id = generate_session_id()
    user_id = request.user_id or generate_user_id()

    chat_service = ChatService(session_id=session_id, user_id=user_id)

    # Store vectors in Redis (retriever will be reconstructed later when needed)
    await chat_service.start_session(request.page_url)

    return SessionResponse(
        session_id=session_id,
        user_id=user_id
    )

@router.post("/ping/model")
async def ping_model(request:PingRequest):
    chat_service = ChatService(
        session_id="ping-test",
        user_id="ping-test"
    )

    return chat_service.ping_custom_model(
        api_key=request.api_key,
        model_name=request.model_name,
        model_temperature=request.model_temperature,
        model_max_tokens=request.model_max_tokens
    )
    

@router.post("/c/{session_id}", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_id = request.user_id or generate_user_id()

    # Reconstruct retriever from session_id using the singleton manager
    # Pass api_key if user provided custom settings
    retriever = vectorstore_manager.get_retriever(
        session_id=session_id, 
        user_id=user_id,
        api_key=request.api_key
    )

    chat_service = ChatService(
        session_id=session_id,
        user_id=user_id,
    )

    result = chat_service.send_message(
        query=request.message,
        retriever_instance=retriever,
        api_key=request.api_key,
        model_name=request.model_name,
        model_temperature=request.model_temperature,
        model_max_tokens=request.model_max_tokens
    )

    return ChatResponse(
        response=result,
        session_id=session_id,
        user_id=user_id,
    )

@router.post("/session/{session_id}/delete")
async def clear(request: Request):
    session_id = request.session_id or generate_session_id()
    user_id = request.user_id or generate_user_id()

    chat_service = ChatService(
        session_id=session_id,
        user_id=user_id,
    )

    chat_service.delete_session()
    return {"message": "History clean successfully"}

@router.get("/session/{session_id}/history", response_model=HistoryResponse)
async def get_history(request: Request):
    session_id = request.session_id or generate_session_id()
    user_id = request.user_id or generate_user_id()

    chat_service = ChatService(
        session_id=session_id,
        user_id=user_id,
    )

    history = chat_service.get_chat_history()

    return HistoryResponse(messages=history, session_id=session_id, user_id=user_id)