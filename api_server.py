import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from dotenv import load_dotenv
import sys
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types
from llama_index.core import VectorStoreIndex, Settings as LlamaSettings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
import speech_recognition as sr
import tempfile



load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI(title="Banking Agent API", version="1.0.0")


security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str
    user_id: str = "user123"

class QueryResponse(BaseModel):
    response: str
    user_id: str


MOCK_USERS = {
    "user123": {
        "username": "user123",
        "password": "password123",  
        "customer_id": "user123"
    },
    "user456": {
        "username": "user3",
        "password": "pass12",  
        "customer_id": "user3"
}
}


agent = None
runner = None
session_service = None

def setup_rag_retriever():
    """Set up RAG retriever."""
    print("Loading RAG system...")
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    LlamaSettings.embed_model = embed_model
    
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = chroma_client.get_collection("bank_products")
    
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    retriever = index.as_retriever(similarity_top_k=3)
    
    print(" RAG system loaded!")
    return retriever

def query_product_knowledge(query: str, retriever) -> str:
    """Query product knowledge base."""
    nodes = retriever.retrieve(query)
    
    if not nodes:
        return "I don't have information about that product. Please contact our customer service for details on products not listed in our standard catalog."
    
    # Check if best match has low relevance score
    if nodes[0].score < 0.3:  
        return "I don't have specific information about that product in our current catalog. Our available products include credit cards, personal loans, home mortgages, auto loans, savings accounts, money market accounts, and CDs. Would you like to know about any of these?"
    
    # Only use high-relevance chunks
    relevant_nodes = [node for node in nodes if node.score >= 0.3]
    
    if not relevant_nodes:
        return "I don't have specific information about that product in our current catalog. Our available products include credit cards, personal loans, home mortgages, auto loans, savings accounts, money market accounts, and CDs. Would you like to know about any of these?"
    
    context = "\n\n".join([node.text for node in relevant_nodes])
    return f"Product Information:\n{context}"


def transcribe_audio(audio_file: UploadFile) -> str:
    """Convert audio file to text using speech recognition."""
    try:
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = audio_file.file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(tmp_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        
        
        os.unlink(tmp_file_path)
        
        return text
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Audio transcription failed: {str(e)}"
        )
    

async def setup_agent():
    """Initialize agent, MCP, and RAG."""
    global agent, runner, session_service
    
    print("Setting up agent...")
    
    
    rag_retriever = setup_rag_retriever()
    
    def search_product_knowledge(query: str) -> str:
        """Search bank product knowledge base."""
        return query_product_knowledge(query, rag_retriever)
    
    
    mcp_toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["mcp_server.py"],
                env=os.environ.copy(),
            )
        )
    )
    
    
    agent = LlmAgent(
    model="gemini-2.5-flash-lite",
    name="banking_assistant",
    instruction=(
        "You are a banking assistant.\n"
        "The authenticated customer ID is provided in square brackets: [Customer ID: xxx]\n"
        "\n"
        "CRITICAL SECURITY RULES:\n"
        "1. You can ONLY access data for the customer ID provided in the brackets.\n"
        "2. If the user asks about ANY other customer ID (user456, user999, etc.), respond:\n"
        "   'I'm sorry, but I can only access information for your account (xxx). "
        "   For security and privacy reasons, I cannot view other customers' data.'\n"
        "3. NEVER call MCP tools with a different customer_id than the one in brackets.\n"
        "\n"
        "For transactions and balances: Use MCP tools with the authenticated customer_id.\n"
        "For product questions: Use search_product_knowledge.\n"
        "Answer clearly and concisely."
    ),
    tools=[mcp_toolset, search_product_knowledge],
)
    
    
    session_service = InMemorySessionService()
    
    
    runner = Runner(
        agent=agent,
        app_name="bank_agent",
        session_service=session_service
    )
    
    print(" Agent ready!")

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup."""
    await setup_agent()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@app.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Login endpoint to get JWT token."""
    user = MOCK_USERS.get(request.username)
    
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/query", response_model=QueryResponse)
async def query_agent(
    request: QueryRequest,
    username: str = Depends(verify_token)
):
    """Query the banking agent (text)."""
    global runner, session_service
    
    if not runner:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    
    try:
        await session_service.create_session(
            app_name="bank_agent",
            user_id=request.user_id,
            session_id=f"session_{request.user_id}"
        )
    except:
        pass  
    
    
    
    context_query = f"[Customer ID: {username}] {request.query}"
    
    content = types.Content(
        role="user",
        parts=[types.Part(text=context_query)]
    )
    
    events = runner.run(
        user_id=request.user_id,
        session_id=f"session_{request.user_id}",
        new_message=content
    )
   
    response_text = ""
    for event in events:
        if event.is_final_response():
            texts = []
            for part in event.content.parts:
                if getattr(part, "text", None):
                    texts.append(part.text)
            response_text = "\n".join(texts).strip()
            break
    
    return QueryResponse(response=response_text, user_id=request.user_id)

@app.post("/query/voice", response_model=QueryResponse)
async def query_agent_voice(
    audio: UploadFile = File(...),
    user_id: str = "user123",
    username: str = Depends(verify_token)
):
    """Query the banking agent with voice input."""
    global runner, session_service
    
    if not runner:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    
    query_text = transcribe_audio(audio)
    print(f"Transcribed: {query_text}")
    
    
    try:
        await session_service.create_session(
            app_name="bank_agent",
            user_id=user_id,
            session_id=f"session_{user_id}"
        )
    except:
        pass
    
  
    context_query = f"[Customer ID: {username}] {query_text}"
    
    content = types.Content(
        role="user",
        parts=[types.Part(text=context_query)]
    )
    
    
    events = runner.run(
        user_id=user_id,
        session_id=f"session_{user_id}",
        new_message=content
    )
    
    # Extract response
    response_text = ""
    for event in events:
        if event.is_final_response():
            texts = []
            for part in event.content.parts:
                if getattr(part, "text", None):
                    texts.append(part.text)
            response_text = "\n".join(texts).strip()
            break
    
    return QueryResponse(response=response_text, user_id=user_id)


    
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "online", "service": "Banking Agent API"}

@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "runner_ready": runner is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
