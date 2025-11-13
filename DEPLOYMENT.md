# Public Deployment Guide for Aurora QA Service

This guide will help you deploy Aurora QA Service to be publicly accessible via a live URL.

## Deploy to Render (100% Free + Public URL)

### Step 1: Prepare Your Repository

1. **Commit all changes:**
   ```bash
   git add .
   git commit -m "Ready for public deployment"
   git push origin main
   ```

### Step 2: Deploy to Render

1. **Go to [render.com](https://render.com)** and sign up (free)
2. **Click "New +"** → **"Web Service"**
3. **Connect your GitHub repository** (`Aurora`)
4. **Render will auto-detect** your `render.yaml` configuration

### Step 3: Configure Environment Variables

In Render dashboard, add these environment variables:

```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Step 4: Deploy

- Click **"Deploy"**
- Wait 3-5 minutes for deployment
- You'll get a public URL like: `https://aurora-qa-service.onrender.com`

## Test Your Public API

Once deployed, your API will be publicly accessible:

```bash
# Health check
curl https://your-app-name.onrender.com/api/v1/health

# Ask a question
curl "https://your-app-name.onrender.com/api/v1/ask?question=Who%20is%20planning%20a%20trip%20to%20Paris?"

# POST request
curl -X POST "https://your-app-name.onrender.com/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
```

## API Documentation

Your API docs will be available at:

- **Swagger UI**: `https://your-app-name.onrender.com/docs`
- **ReDoc**: `https://your-app-name.onrender.com/redoc`

## 🔍 Example Public URLs

After deployment, you'll have:

- **Base URL**: `https://aurora-qa-service-xyz.onrender.com`
- **Ask API**: `https://aurora-qa-service-xyz.onrender.com/api/v1/ask`
- **Health**: `https://aurora-qa-service-xyz.onrender.com/api/v1/health`
- **Docs**: `https://aurora-qa-service-xyz.onrender.com/docs`

## Important Notes

### Free Tier Limitations:

- **Sleep Mode**: App sleeps after 15 minutes of inactivity
- **Cold Start**: First request after sleep takes 15-30 seconds
- **Memory**: 512MB RAM limit
- **Bandwidth**: Unlimited (for free tier)

### For Production Use:

- Upgrade to paid plan ($7/month) for:
  - No sleep mode
  - More memory (up to 4GB)
  - Faster CPU
  - Custom domains

## Troubleshooting

### If deployment fails:

1. **Check logs** in Render dashboard
2. **Verify dependencies** in `requirements.txt`
3. **Check environment variables** are set correctly

### If API is slow:

- First request after sleep is always slow (15-30s)
- Subsequent requests are fast (<2s)

### Keep your service awake (optional):

Use a simple ping service to prevent sleep:

```bash
# Ping every 10 minutes
*/10 * * * * curl https://your-app-name.onrender.com/api/v1/health
```

## Success!

Once deployed, your Aurora QA Service will be:

- **Publicly accessible** via HTTPS
- **Free to host** (only pay for OpenAI API usage)
- **Professionally documented** with Swagger UI
- **Production-ready** with health checks and error handling

Share your public API URL with anyone and they can ask questions!
