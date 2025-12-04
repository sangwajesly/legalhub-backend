# LegalHub Backend - Deployment Guide

## 🎯 Quick Start (Render Deployment)

### Current Issue Fixed
The application was exceeding Render's 8GB memory limit during build due to heavy ML packages. This has been fixed by splitting dependencies.

### Deploy to Render (Recommended)

1. **Use the `render-deploy-fix` branch** (you're here!)

2. **In Render Dashboard:**
   - Connect your GitHub repository
   - Select branch: `render-deploy-fix`
   - Render will auto-detect `render.yaml`
   - Add environment variables (see below)
   - Deploy!

3. **Environment Variables Required:**
   ```
   DATABASE_URL=your_database_url
   FIREBASE_CREDENTIALS=your_firebase_json
   GOOGLE_API_KEY=your_google_api_key
   JWT_SECRET_KEY=your_secret_key
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

---

## 📦 Dependencies Structure

### requirements-production.txt
**Size:** ~50MB installed
**Build time:** 3-5 minutes
**Memory usage:** ~2-3GB during build

Contains:
- FastAPI and core web framework
- Authentication (JWT, OAuth)
- Firebase integration
- Database (SQLAlchemy)
- HTTP clients

**This is what Render will install by default.**

### requirements-ai.txt
**Size:** ~3GB installed
**Build time:** 15-20 minutes
**Memory usage:** ~8-10GB during build

Contains:
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- LangChain (AI orchestration)
- PyTorch (via dependencies)

**⚠️ Only install if you have:**
- Render Pro plan ($25/month) or higher
- Or use a separate service for AI features

### requirements-dev.txt
Development tools (not needed in production):
- Black, Flake8 (code formatting)
- MyPy (type checking)
- Pytest (testing)

---

## 🏗️ Architecture Options

### Option 1: Core API Only (Current Setup)
✅ Recommended for MVP and free tier

```
┌─────────────────┐
│  Render Free    │
│  Core API       │
│  - Auth         │
│  - Bookings     │
│  - Cases        │
│  - Users        │
└─────────────────┘
```

**Pros:**
- Deploys successfully on free tier
- Fast build times
- Low memory usage

**Cons:**
- AI chatbot disabled
- No vector search

### Option 2: Separate AI Service
✅ Recommended for production

```
┌─────────────────┐     ┌──────────────────┐
│  Render         │────▶│  Railway/Modal   │
│  Core API       │     │  AI Service      │
│                 │◀────│  - Chatbot       │
└─────────────────┘     │  - Embeddings    │
                        │  - Vector Search │
                        └──────────────────┘
```

**Implementation:**
1. Deploy core API to Render (this repo)
2. Deploy AI service separately:
   - **Railway:** Better ML support, ~$5-10/month
   - **Modal:** Serverless ML, pay per use
   - **Hugging Face Spaces:** Free GPU inference

3. Core API calls AI service via HTTP:
   ```python
   # In your main API
   AI_SERVICE_URL = os.getenv("AI_SERVICE_URL")
   response = requests.post(f"{AI_SERVICE_URL}/chat", json=data)
   ```

### Option 3: Monolithic on Render Pro
💰 Requires paid plan

```
┌─────────────────┐
│  Render Pro     │
│  Full Stack     │
│  - Core API     │
│  - AI Features  │
│  - Vector DB    │
└─────────────────┘
```

**Cost:** $25/month minimum
**Setup:**
1. Upgrade to Render Pro
2. Uncomment AI dependencies in `render.yaml`:
   ```yaml
   buildCommand: |
     pip install -r requirements-production.txt
     pip install -r requirements-ai.txt  # Uncomment this
   ```

---

## 🔧 Making AI Features Optional in Code

Update your application to handle missing AI dependencies gracefully:

```python
# app/main.py
try:
    from app.services.ai_service import AIService
    from app.api.endpoints import chatbot
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("⚠️  AI features disabled - missing dependencies")

app = FastAPI(
    title="LegalHub API",
    description="Legal assistance platform" + 
                (" with AI" if AI_ENABLED else "")
)

# Conditionally include AI routes
if AI_ENABLED:
    app.include_router(chatbot.router, prefix="/api/v1/chatbot")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ai_enabled": AI_ENABLED,
        "features": {
            "auth": True,
            "bookings": True,
            "cases": True,
            "chatbot": AI_ENABLED
        }
    }
```

---

## 🚀 Deployment Steps

### Step 1: Merge This Branch
```bash
# Review changes
git checkout render-deploy-fix
git diff main

# If everything looks good, merge to main
git checkout main
git merge render-deploy-fix
git push origin main
```

### Step 2: Configure Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. New Web Service → Connect Repository
3. Select `legalhub-backend`
4. Render auto-detects `render.yaml` ✅
5. Add environment variables
6. Deploy!

### Step 3: Verify Deployment
```bash
# Check health endpoint
curl https://your-app.onrender.com/health

# Should return:
{
  "status": "healthy",
  "ai_enabled": false,
  "features": {...}
}
```

### Step 4: (Optional) Add AI Service
If you want AI features:
- Deploy AI service separately (see Option 2)
- Or upgrade to Render Pro (see Option 3)

---

## 🐛 Troubleshooting

### Build Still Failing?

**Error: "Out of memory"**
- Make sure you're using `requirements-production.txt`
- Check that `requirements-ai.txt` is NOT being installed
- Verify `render.yaml` is in the root directory

**Error: "Module not found"**
- Some imports might be trying to use AI features
- Make imports conditional (see code example above)
- Check all files in `app/` directory

**Error: "Firebase credentials invalid"**
- Add `FIREBASE_CREDENTIALS` as environment variable
- Format: Full JSON content of your service account key

### Still Having Issues?

1. **Check Render logs:**
   - Dashboard → Your Service → Logs
   - Look for specific error messages

2. **Test locally:**
   ```bash
   pip install -r requirements-production.txt
   uvicorn app.main:app --reload
   ```

3. **Alternative platforms:**
   - **Railway:** More memory, better ML support
   - **Fly.io:** More flexible, similar pricing
   - **Google Cloud Run:** Serverless, pay per use

---

## 📊 Cost Comparison

| Platform | Plan | Memory | AI Support | Cost |
|----------|------|--------|------------|------|
| Render Free | 512MB | ❌ | No | $0 |
| Render Starter | 512MB | ❌ | No | $7/mo |
| Render Pro | 4GB | ✅ | Yes | $25/mo |
| Railway | 8GB | ✅ | Yes | ~$5-10/mo |
| Modal | Serverless | ✅ | Yes | Pay per use |

---

## 🎉 Success!

Once deployed, your API will be available at:
```
https://legalhub-backend.onrender.com
```

Test it:
```bash
curl https://legalhub-backend.onrender.com/docs
```

You should see the FastAPI interactive documentation! 🚀