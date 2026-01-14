# Bank Agent API Documentation

## Overview
This API exposes a banking customer service assistant built with FastAPI and Google ADK.
All protected endpoints require JWT bearer authentication.

## Authentication

### POST /login
Authenticate a user and receive a JWT access token.

**Request Body**
```json
{
  "username": "user123",
  "password": "password123"
}
```

**Response**
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

## Agent Interaction

### POST /query
Submit a text query to the banking agent.

**Headers**
```
Authorization: Bearer <JWT_TOKEN>
```

**Request Body**
```json
{
  "query": "What is my checking account balance?",
  "user_id": "user123"
}
```

**Response**
```json
{
  "response": "Your current checking account balance is ...",
  "user_id": "user123"
}
```

### POST /query/voice
Submit a voice query to the banking agent.

**Headers**
```
Authorization: Bearer <JWT_TOKEN>
```

**Form Data**
- audio: WAV audio file
- user_id: user identifier

**Response**
```json
{
  "response": "Here is the information you requested ...",
  "user_id": "user123"
}
```

## Health

### GET /health
Returns service readiness information.

**Response**
```json
{
  "status": "healthy",
  "agent_ready": true,
  "runner_ready": true
}
```

## Error Handling

- 401 Unauthorized: Missing or invalid JWT
- 503 Service Unavailable: Agent not initialized
- 400 Bad Request: Invalid input or transcription error

## Notes
- Customer identity is derived from the JWT token subject.
- The agent automatically selects the appropriate tool or retriever.
