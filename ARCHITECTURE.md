# Architecture Overview

## System Architecture

The Aurora QA Service follows a microservice architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Layer (routes.py)                   │   │
│  │  - GET/POST /api/v1/ask                              │   │
│  │  - GET /api/v1/health                                │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Service Layer (qa_service.py)              │   │
│  │  - Orchestrates the RAG pipeline                     │   │
│  │  - Coordinates message retrieval, embedding, and LLM │   │
│  └──────┬───────────────┬───────────────┬───────────────┘   │
│         │               │               │                    │
│         ▼               ▼               ▼                    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Message  │  │  Embedding   │  │     LLM      │          │
│  │ Service  │  │   Service    │  │   Service    │          │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘          │
│       │               │                  │                   │
└───────┼───────────────┼──────────────────┼───────────────────┘
        │               │                  │
        ▼               ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Messages    │  │  Sentence    │  │   OpenAI     │
│  API         │  │ Transformers │  │     API      │
│  /messages   │  │   Model      │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Component Details

### 1. API Layer (`app/api/routes.py`)

- **Responsibility**: Handle HTTP requests and responses
- **Endpoints**:
  - `GET /api/v1/ask?question=...` - Answer questions (GET)
  - `POST /api/v1/ask` - Answer questions (POST)
  - `GET /api/v1/health` - Health check
- **Features**:
  - Request validation
  - Error handling
  - Response formatting

### 2. Service Layer

#### 2.1 QA Service (`app/services/qa_service.py`)

- **Responsibility**: Orchestrate the RAG pipeline
- **Process**:
  1. Fetch messages from Messages API
  2. Format messages for embedding
  3. Retrieve relevant messages using semantic search
  4. Generate answer using LLM
  5. Extract source message IDs
- **Error Handling**: Comprehensive error handling and logging

#### 2.2 Message Service (`app/services/message_service.py`)

- **Responsibility**: Fetch and format messages from Messages API
- **Features**:
  - HTTP client with timeout handling
  - Message formatting for search
  - Error handling and retry logic

#### 2.3 Embedding Service (`app/services/embedding_service.py`)

- **Responsibility**: Generate embeddings and perform semantic search
- **Features**:
  - Sentence transformer model loading
  - Embedding generation
  - Cosine similarity calculation
  - Top-K message retrieval

#### 2.4 LLM Service (`app/services/llm_service.py`)

- **Responsibility**: Generate answers using LLM
- **Features**:
  - OpenAI API integration
  - Prompt engineering
  - JSON response parsing
  - Retry logic with exponential backoff

### 3. Data Models (`app/models.py`)

- **Message**: Message model from Messages API
- **QuestionRequest**: Request model for QA endpoint
- **AnswerResponse**: Response model for QA endpoint
- **ErrorResponse**: Error response model

### 4. Configuration (`app/config.py`)

- **Responsibility**: Manage application configuration
- **Features**:
  - Environment variable support
  - Type validation with Pydantic
  - Default values
  - Configuration documentation

### 5. Utilities

#### 5.1 Logger (`app/utils/logger.py`)

- **Responsibility**: Structured logging
- **Features**:
  - JSON-formatted logs
  - Log levels
  - Contextual logging

#### 5.2 Exceptions (`app/utils/exceptions.py`)

- **Responsibility**: Custom exception classes
- **Features**:
  - HTTP exception mapping
  - Error messages
  - Status code handling

## Data Flow

### Question Answering Pipeline

1. **Request**: Client sends question to `/api/v1/ask`
2. **Validation**: API layer validates request
3. **Message Retrieval**: Message service fetches all messages
4. **Embedding Generation**: Embedding service generates embeddings for question and messages
5. **Semantic Search**: Top-K relevant messages are retrieved
6. **Answer Generation**: LLM service generates answer from relevant messages
7. **Response**: Answer and source IDs are returned to client

### Example Flow

```
Question: "When is Layla planning her trip to London?"

1. Fetch Messages:
   - Message 1: "I am planning my trip to London next month."
   - Message 2: "That sounds great! When exactly are you going?"
   - Message 3: "I will be there from February 1st to February 15th."

2. Generate Embeddings:
   - Question embedding: [0.1, 0.2, ..., 0.9]
   - Message embeddings: [[0.2, 0.1, ...], [...], [...]]

3. Calculate Similarities:
   - Message 3: 0.95 (highest similarity)
   - Message 1: 0.85
   - Message 2: 0.60

4. Retrieve Top-K (K=5):
   - Top messages: [Message 3, Message 1, Message 2]

5. Generate Answer:
   - LLM receives question + top messages
   - LLM generates: "Layla is planning her trip to London from February 1st to February 15th."

6. Return Response:
   {
     "answer": "Layla is planning her trip to London from February 1st to February 15th.",
     "sources": ["3", "1"]
   }
```

## Design Patterns

### 1. Service Layer Pattern

- **Purpose**: Separate business logic from API layer
- **Benefits**: Testability, reusability, maintainability

### 2. Dependency Injection

- **Purpose**: Loose coupling between components
- **Implementation**: Service instances injected into API routes

### 3. Retry Pattern

- **Purpose**: Handle transient failures
- **Implementation**: Tenacity library for LLM API calls

### 4. Factory Pattern

- **Purpose**: Create service instances based on configuration
- **Implementation**: LLM service factory based on provider

## Scalability Considerations

### Current Limitations

1. **In-Memory Processing**: All messages are processed in memory
2. **Synchronous Embedding**: Embeddings generated synchronously
3. **No Caching**: No caching of embeddings or messages

### Future Improvements

1. **Caching**: Cache embeddings and messages
2. **Async Processing**: Async embedding generation
3. **Database**: Store messages and embeddings in database
4. **Queue System**: Use message queue for async processing
5. **Load Balancing**: Multiple service instances
6. **CDN**: Cache static resources

## Security Considerations

### Current Implementation

1. **API Keys**: Stored in environment variables
2. **CORS**: Configurable CORS middleware
3. **Input Validation**: Pydantic models for validation
4. **Error Handling**: No sensitive data in error messages

### Recommended Improvements

1. **Authentication**: Add API key authentication
2. **Rate Limiting**: Implement rate limiting
3. **Input Sanitization**: Sanitize user inputs
4. **Secrets Management**: Use secret management service
5. **HTTPS**: Enforce HTTPS in production
6. **Logging**: Avoid logging sensitive data

## Monitoring and Observability

### Current Implementation

1. **Structured Logging**: JSON-formatted logs
2. **Health Check**: Health check endpoint
3. **Error Tracking**: Comprehensive error logging

### Recommended Additions

1. **Metrics**: Prometheus metrics
2. **Tracing**: Distributed tracing (OpenTelemetry)
3. **Alerting**: Alert on errors and performance issues
4. **Dashboards**: Monitoring dashboards
5. **Log Aggregation**: Centralized log aggregation

