# 🏦 Bank Agent – ADK-Based Banking Assistant

A production-style **banking customer service agent** built using **Google Agent Development Kit (ADK)**.  
The system exposes a secure **FastAPI** backend, performs **tool calling via MCP**, and integrates **Retrieval-Augmented Generation (RAG)** for bank product knowledge.

This project demonstrates how to design, implement, and test a **real-world, tool-using AI agent** suitable for enterprise and interview evaluation scenarios.

---

## ✨ Key Features

- **ADK-based LLM agent**
  - Automatic intent routing (transactions vs. products)
  - Tool calling without user prompts or hard-coded flows

- **Secure REST API**
  - JWT authentication
  - Protected endpoints for customer queries

- **MCP (Model Context Protocol) integration**
  - Stdio-based MCP server
  - SQLite-backed tools for:
    - Last transaction
    - Recent transactions
    - Account balance

- **RAG for product knowledge**
  - ChromaDB vector store
  - LlamaIndex retriever
  - HuggingFace sentence embeddings

- **Voice & text support**
  - Text queries via REST
  - Voice queries via audio upload and transcription

- **Production-style reliability**
  - Graceful handling of empty responses
  - Rate-limit protection
  - Deterministic response extraction from ADK events

---

## 🧠 High-Level Architecture

```
Client
  |
  |  REST (JWT)
  v
FastAPI API Server
  |
  |  ADK Runner
  v
ADK LLM Agent
  |                |
  | MCP Tool Calls | RAG Search
  v                v
MCP Stdio Server   ChromaDB + LlamaIndex
(SQLite)           (Product Knowledge)
```

A detailed architecture breakdown is provided in **Architecture_Documentation.pdf**.

---

## 📁 Repository Structure

```
.
├── api_server.py              # FastAPI app + ADK agent runner
├── mcp_server.py              # MCP stdio server (SQLite-backed tools)
├── bank_data.db               # SQLite transactions database
├── chroma_db/                 # Persistent ChromaDB store
├── scripts/
│   ├── seed_sqlite.py         # Create & seed transaction DB
│   └── build_rag_chroma.py    # Build product knowledge base
├── docs/
│   └── api.md                 # API documentation & test cases
└── README.md
```

---

## 🔐 Authentication

- JWT Bearer authentication
- Token issued via `/login`
- Token subject (`sub`) is used as the **customer identifier**
- The user never specifies their ID manually

---

## 🚀 Running the Project

### 1️⃣ Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Set environment variables

```bash
export JWT_SECRET_KEY="change-me"
export ADK_MODEL="openai/gpt-4o-mini"
export SQLITE_PATH="./bank_data.db"
export CHROMA_PATH="./chroma_db"
```

### 3️⃣ Start MCP server

```bash
python mcp_server.py
```

### 4️⃣ Start API server

```bash
uvicorn api_server:app --reload
```

---

## 🔌 API Endpoints

- `POST /login` – Authenticate and receive JWT
- `POST /query` – Text-based agent query
- `POST /query/voice` – Voice-based agent query
- `GET /health` – Health check

Interactive docs available at: `http://localhost:8000/docs`

---

## 🧪 Test Coverage

Included test scenarios:

1. Last transaction query  
2. Product inquiry (RAG)  
3. Unauthorized API request  
4. Invalid customer identifier  
5. Multiple transactions on same day  
6. Unknown product handling  
7. Noisy audio transcription  
8. Concurrent ADK agent requests  

---

## 🧩 Design Decisions

- **ADK over manual orchestration** – model-driven tool selection
- **MCP isolation** – transactional logic separated from reasoning
- **RAG for static knowledge** – reduces hallucinations
- **JWT-derived identity** – prevents client-side ID spoofing

---

## Build the RAG knowledge base (ChromaDB)
The vector store is generated locally and is not committed to the repo.
python setup_rag.py

And for the SQLite DB:
## Build the transactions database (SQLite)
python database.py

## ⚠️ Disclaimer

This project uses mock users and local storage for demonstration purposes only.  
It is **not intended for production banking systems** without additional security hardening.

