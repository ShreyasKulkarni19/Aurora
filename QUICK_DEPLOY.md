# 🚀 Quick Deployment Guide - Aurora QA Service

Your code is ready for deployment! Follow these steps to make your `/ask` API publicly accessible.

## Step 1: Deploy to Render (5 minutes)

### 1. Go to Render

- Visit [render.com](https://render.com)
- Sign up/Login with GitHub

### 2. Create Web Service

- Click **"New +"** → **"Web Service"**
- Select **"Build and deploy from a Git repository"**
- Connect to **"Aurora"** repository
- Render will auto-detect your `render.yaml`

### 3. Configure Service

- **Name**: `aurora-qa-service` (or your preferred name)
- **Plan**: Select **"Free"**
- All other settings are auto-configured from `render.yaml`

### 4. Add Environment Variable

**CRITICAL**: Add your OpenAI API key:

- In the **Environment** section
- Add: `OPENAI_API_KEY` = `sk-your-openai-api-key-here`

### 5. Deploy

- Click **"Create Web Service"**
- Wait 3-5 minutes for deployment
- You'll get a public URL like: `https://aurora-qa-service-xyz.onrender.com`

## Step 2: Test Your Public API

Once deployed, test the endpoint:

```bash
# Health Check
curl https://your-url.onrender.com/api/v1/health

# Ask a Question (GET)
curl "https://your-url.onrender.com/api/v1/ask?question=Who%20is%20planning%20a%20trip%20to%20Paris?"

# Ask a Question (POST)
curl -X POST "https://your-url.onrender.com/api/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "Who is planning a trip to Paris?"}'
```

## Expected Response:

```json
{
  "answer": "Fatima El-Tahir, Armand Dupont, and Thiago Monteiro are planning trips to Paris."
}
```

## Step 3: Share with Evaluator

Give the evaluator:

- **API URL**: `https://your-url.onrender.com/api/v1/ask`
- **Method**: GET or POST
- **Parameter**: `question` (string)
- **Documentation**: `https://your-url.onrender.com/docs`

## Important Notes:

- **Free Tier**: May sleep after 15 minutes of inactivity
- **Cold Start**: First request after sleep takes 15-30 seconds
- **Subsequent requests**: Fast (<2 seconds)
- **Cost**: Only OpenAI API usage (~$0.01-0.05 per query)

## API Endpoints Available:

- `GET/POST /api/v1/ask` - Main QA endpoint
- `GET /api/v1/health` - Health check
- `GET /docs` - Interactive API documentation
- `POST /api/v1/refresh-cache` - Refresh data cache

## 🎉 That's it! Your Aurora QA Service is now publicly accessible!
