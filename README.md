# Aurora QA Service

A production-grade Question Answering API service that uses Retrieval-Augmented Generation (RAG) to answer natural language questions based on member messages.

## Approach Considerations & Design Decisions

When building this question-answering system, I evaluated several architectural approaches to ensure the best balance of accuracy, performance, and maintainability.

### Alternative Approaches Considered

#### 1. **Fine-tuned Language Model**

**Approach**: Train a specialized LLM on the member messages dataset.

**Pros**:

- High accuracy for domain-specific queries
- No need for retrieval pipeline
- Potentially faster inference once trained

**Cons**:

- Requires large datasets (thousands of examples)
- Expensive training process (GPU resources, time)
- Limited to training data cutoff (can't handle new messages without retraining)
- Risk of hallucination with outdated information
- Complex model versioning and deployment

#### 2. **Semantic Search Only (No LLM)**

**Approach**: Use only embedding similarity to return the most relevant messages.

**Pros**:

- Simple implementation
- Fast response times
- No API costs for LLM inference
- Always returns actual message content

**Cons**:

- No natural language answer generation
- Poor user experience (raw message snippets)
- Inability to synthesize information across multiple messages
- Limited reasoning capabilities

#### 3. **Traditional Keyword Search (Elasticsearch/Solr)**

**Approach**: Use inverted index-based search engines with TF-IDF scoring.

**Pros**:

- Excellent keyword matching precision
- Fast query performance
- Battle-tested technology
- Good for exact phrase matching

**Cons**:

- Poor handling of semantic similarity
- Struggles with synonyms and paraphrasing
- No understanding of context or intent
- Requires extensive query optimization

#### 4. **Hybrid: Knowledge Graph + RAG**

**Approach**: Extract entities and relationships to build a knowledge graph, then combine with RAG.

**Pros**:

- Rich relationship understanding
- Excellent for complex reasoning queries
- Handles entity disambiguation well
- Supports logical inference

**Cons**:

- Complex implementation and maintenance
- Requires domain expertise for ontology design
- High computational overhead for graph traversal
- Entity extraction accuracy challenges

### **Chosen Approach: Hybrid Search + RAG**

I selected a **hybrid semantic-keyword search combined with RAG** for the following reasons:

#### **Why This Approach Works Best**

1. **Balanced Precision & Recall**: Semantic embeddings capture intent while keyword matching ensures exact term relevance
2. **Practical Implementation**: Leverages proven technologies (sentence transformers + OpenAI) without complex infrastructure
3. **Cost Effective**: Reasonable balance between accuracy and API costs
4. **Maintainable**: Clean architecture with separation of concerns
5. **Extensible**: Easy to swap LLM providers or add new retrieval methods

#### **Key Technical Decisions**

- **70% Embedding Weight / 30% Keyword Weight**: Optimized through experimentation
- **Top-50 Message Retrieval**: Ensures comprehensive coverage for "list all" type questions
- **Caching Strategy**: 24-hour embedding cache + 5-minute message cache for performance
- **all-MiniLM-L6-v2**: Balanced model for speed vs accuracy trade-offs

### **Future Enhancement: Knowledge-Based RAG**

Given additional resources and time, I would implement **Knowledge-Based RAG** to significantly enhance the system:

#### **Proposed Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                Knowledge-Enhanced RAG                    │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐ │
│  │   Entity    │    │  Relation    │    │  Temporal   │ │
│  │ Extraction  │    │ Extraction   │    │ Reasoning   │ │
│  │  (NER+REL)  │    │ (OpenIE/RE)  │    │ (TimeGraph) │ │
│  └─────┬───────┘    └───────┬──────┘    └──────┬──────┘ │
│        │                    │                  │        │
│        └────────────────────┼──────────────────┘        │
│                             │                           │
│  ┌─────────────────────────▼─────────────────────────┐  │
│  │            Knowledge Graph                        │  │
│  │    (Neo4j/ArangoDB with Rich Ontology)           │  │
│  └─────────────────────┬───────────────────────────┘  │
│                        │                             │
│  ┌────────────────────▼──────────────────────────┐   │
│  │        Multi-Modal Retrieval                  │   │
│  │  • Graph Traversal (Cypher Queries)          │   │
│  │  • Vector Similarity (Current Method)        │   │
│  │  • Structured Queries (SQL-like)             │   │
│  └─────────────────┬─────────────────────────────┘   │
│                    │                                 │
│  ┌────────────────▼─────────────────────────────┐   │
│  │         Context-Aware LLM                    │   │
│  │  • Structured prompts with graph context     │   │
│  │  • Multi-hop reasoning capabilities          │   │
│  │  • Confidence scoring for answers            │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

#### **Implementation Plan**

**Phase 1: Entity & Relationship Extraction**

- Deploy spaCy/Stanza for Named Entity Recognition
- Implement OpenIE for relationship extraction
- Build entity disambiguation pipeline
- Create initial knowledge schema

**Phase 2: Knowledge Graph Construction**

- Set up Neo4j/ArangoDB infrastructure
- Design domain-specific ontology (Person, Location, Event, etc.)
- Implement automated graph population pipeline
- Build graph validation and quality metrics

**Phase 3: Enhanced Retrieval**

- Develop graph traversal algorithms for complex queries
- Implement multi-hop reasoning paths
- Build hybrid retrieval combining graph + vector search
- Create query planning and optimization

**Phase 4: Advanced Reasoning**

- Implement temporal reasoning for time-based queries
- Add graph-aware prompt engineering for LLMs
- Build confidence scoring and answer verification
- Create explanation generation for reasoning paths

#### **Expected Benefits**

1. **Complex Query Handling**: "Who knows someone in Paris who can help with restaurant recommendations?"
2. **Temporal Reasoning**: "What was discussed about the London trip before the hotel booking?"
3. **Relationship Inference**: "Find people who have traveled together in the past"
4. **Disambiguation**: Distinguish between multiple people with similar names using context
5. **Explainable Answers**: Provide reasoning paths for complex answers

## This knowledge-based approach would transform Aurora from a document search system into an intelligent reasoning engine capable of understanding complex relationships and temporal patterns within member communications.

## Current Features

- **RAG Pipeline**: Combines semantic retrieval with LLM-based answer generation
- **Semantic Search**: Uses sentence transformers for embedding-based message retrieval
- **LLM Integration**: Supports OpenAI and extensible to other providers
- **Microservice Architecture**: Clean, modular, and production-ready
- **FastAPI**: Modern, fast, and type-safe API framework
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Structured Logging**: Comprehensive logging with structlog
- **Error Handling**: Robust error handling and retry logic

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP Request
       │ /ask?question=...
       ▼
┌─────────────────────────────────────┐
│         FastAPI Application         │
│  ┌───────────────────────────────┐  │
│  │      API Routes (/ask)        │  │
│  └──────────────┬────────────────┘  │
│                 │                    │
│                 ▼                    │
│  ┌───────────────────────────────┐  │
│  │        QA Service             │  │
│  └──────────────┬────────────────┘  │
│                 │                    │
│    ┌────────────┼────────────┐      │
│    │            │            │      │
│    ▼            ▼            ▼      │
│  ┌──────┐  ┌──────────┐  ┌──────┐  │
│  │Message│  │Embedding│  │ LLM  │  │
│  │Service│  │ Service │  │Service│  │
│  └───┬──┘  └────┬─────┘  └───┬──┘  │
│      │           │            │      │
└──────┼───────────┼────────────┼──────┘
       │           │            │
       ▼           │            │
┌──────────────┐   │            │
│ Messages API │   │            │
│  /messages   │   │            │
└──────────────┘   │            │
                   │            │
           ┌───────┘            │
           │                    │
      ┌────▼─────┐         ┌────▼────┐
      │Sentence  │         │ OpenAI  │
      │Transform │         │   API   │
      │  Model   │         │         │
      └──────────┘         └─────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- OpenAI API key (or configure another LLM provider)

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd Aurora
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. Run the service:

```bash
python -m app.main
```

Or using Docker Compose:

```bash
docker-compose up --build
```

### Usage

#### Ask a Question (GET)

```bash
curl "http://localhost:8000/api/v1/ask?question=Who%20is%20planning%20a%20trip%20to%20Paris?"
```

#### Ask a Question (POST)

```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is planning a trip to Paris?"}'
```

#### Response

```json
{
  "answer": "Sophia Al-Farsi is planning a trip to Paris on Friday.",
  "sources": ["b1e9bb83-18be-4b90-bbb8-83b7428e8e21"]
}
```

## Configuration

### Environment Variables

- `MESSAGES_API_URL`: URL of the messages API endpoint (default: `https://november7-730026606190.europe-west1.run.app/messages/`)
- `OPENAI_API_KEY`: OpenAI API key (required)
- `LLM_PROVIDER`: LLM provider (default: `openai`)
- `EMBEDDING_MODEL`: Sentence transformer model (default: `all-MiniLM-L6-v2`)
- `TOP_K_MESSAGES`: Number of top relevant messages to retrieve (default: `5`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

See `.env.example` for all available configuration options.

## API Endpoints

### GET/POST `/api/v1/ask`

Answer a natural language question.

**Query Parameters (GET):**

- `question` (required): Natural language question

**Request Body (POST):**

```json
{
  "question": "When is Layla planning her trip to London?"
}
```

**Response:**

```json
{
  "answer": "Layla is planning her trip to London from February 1st to February 15th.",
  "sources": ["3", "1"]
}
```

### GET `/api/v1/health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "service": "aurora-qa-service"
}
```

## Development

### Project Structure

```
Aurora/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── message_service.py    # Message API integration
│   │   ├── embedding_service.py  # Embedding generation
│   │   ├── llm_service.py        # LLM integration
│   │   └── qa_service.py         # Main QA orchestrator
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # Logging configuration
│       └── exceptions.py    # Custom exceptions
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Docker

Build and run with Docker:

```bash
docker build -t aurora-qa-service .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key aurora-qa-service
```

### Docker Compose

```bash
docker-compose up -d
```

### Production Considerations

1. **Environment Variables**: Use secure secret management (e.g., AWS Secrets Manager, HashiCorp Vault)
2. **API Keys**: Never commit API keys to version control
3. **CORS**: Configure CORS appropriately for your frontend
4. **Rate Limiting**: Add rate limiting middleware
5. **Monitoring**: Add application monitoring (e.g., Prometheus, Datadog)
6. **Scaling**: Use a process manager (e.g., Gunicorn with multiple workers)
7. **Database**: Consider caching embeddings and messages for better performance
8. **Error Tracking**: Integrate error tracking (e.g., Sentry)

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
