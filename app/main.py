from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router

app = FastAPI(
	title="AI Chat Assistant Backend",
	description="Backend API for Chrome Extension Chatbot with RAG and session management",
	version="1.0.0"
)

# Allow CORS for local frontend development
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Health check endpoint
@app.get("/ping")
def ping():
	return {"status": "ok"}

# Main API routes
app.include_router(router)