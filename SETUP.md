# Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Copy the example (if available) or create manually
cp .env.example .env
```

Edit `.env` and set your configuration:

```env
# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Messages API URL (default: https://november7-730026606190.europe-west1.run.app/messages/)
MESSAGES_API_URL=https://november7-730026606190.europe-west1.run.app/messages/

# Optional: LLM Model (default: gpt-4-turbo-preview)
OPENAI_MODEL=gpt-4-turbo-preview

# Optional: Number of relevant messages to retrieve (default: 5)
TOP_K_MESSAGES=5
```

### 3. Start the Service

#### Option A: Run Locally

```bash
# Using the run script
python run.py

# Or directly with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option B: Using Docker Compose

```bash
# Build and start all services (including mock messages API)
docker-compose up --build

# Or in detached mode
docker-compose up -d
```

#### Option C: Using Docker

```bash
# Build the image
docker build -t aurora-qa-service .

# Run the container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e MESSAGES_API_URL=https://november7-730026606190.europe-west1.run.app/messages/ \
  aurora-qa-service
```

### 4. Test the Service

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test ask endpoint
curl "http://localhost:8000/api/v1/ask?question=When%20is%20Layla%20planning%20her%20trip%20to%20London?"

# Or use the test script
python test_service.py
```

### 5. Access API Documentation

Open your browser and navigate to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `MESSAGES_API_URL` | URL of the messages API | `https://november7-730026606190.europe-west1.run.app/messages/` |
| `LLM_PROVIDER` | LLM provider | `openai` |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4-turbo-preview` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `TOP_K_MESSAGES` | Number of relevant messages | `5` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Server port | `8000` |

### Supported OpenAI Models

- `gpt-4-turbo-preview` (default, recommended)
- `gpt-4`
- `gpt-3.5-turbo`
- `gpt-4-1106-preview`

### Supported Embedding Models

- `all-MiniLM-L6-v2` (default, fast and efficient)
- `all-mpnet-base-v2` (better quality, slower)
- `all-MiniLM-L12-v2` (balanced)

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Make sure `OPENAI_API_KEY` is set in `.env` file
   - Verify the API key is valid

2. **Messages API Connection Error**
   - Check if the messages API is running
   - Verify `MESSAGES_API_URL` is correct
   - Check network connectivity

3. **Embedding Model Download**
   - The first run will download the embedding model (~80MB)
   - Ensure you have internet connection
   - Check disk space

4. **Port Already in Use**
   - Change the `PORT` in `.env` file
   - Or stop the service using the port

5. **Docker Build Fails**
   - Check Docker is running
   - Verify Dockerfile is correct
   - Check disk space

## Production Deployment

### Requirements

1. **Environment Variables**: Use secure secret management
2. **API Keys**: Never commit API keys to version control
3. **CORS**: Configure CORS appropriately
4. **Rate Limiting**: Add rate limiting middleware
5. **Monitoring**: Add application monitoring
6. **Scaling**: Use a process manager (e.g., Gunicorn)
7. **Database**: Consider caching for better performance
8. **Error Tracking**: Integrate error tracking (e.g., Sentry)

### Example Production Setup

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Next Steps

1. Configure your messages API endpoint
2. Set up monitoring and logging
3. Add rate limiting
4. Configure CORS for your frontend
5. Set up CI/CD pipeline
6. Add unit and integration tests

