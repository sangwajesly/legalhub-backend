# 🚀 Quick Start: Deploy to Render

## Before You Start
✅ You have a Render account  
✅ Your GitHub repo is connected to Render  
✅ You have your environment variables ready  

---

## Step 1: Merge the Fix 

**Option A: Auto-merge (if you trust the changes)**
```bash
# This PR fixes your memory issues
# Just merge it from GitHub UI
```

**Option B: Review first (recommended)**
1. Go to: https://github.com/sangwajesly/legalhub-backend/pull/2
2. Review the changes
3. Click "Merge pull request"

---

## Step 2: Deploy to Render

### 2.1 Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your `legalhub-backend` repository
4. Render will auto-detect the `render.yaml` file ✨

### 2.2 Configure (if render.yaml not detected)

If Render doesn't detect the config automatically:

**Build Command:**
```bash
pip install --upgrade pip setuptools wheel && pip install --no-cache-dir -r requirements-production.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Environment:**
- Environment: `Python 3`
- Region: `Oregon` (or closest to you)
- Branch: `main` (after merging the PR)

---

## Step 3: Add Environment Variables

Click "Environment" tab and add these variables:

### Required Variables:
```
PYTHON_VERSION=3.10.0
PORT=8001
PYTHONUNBUFFERED=1
```

### Your App Variables:
```
# Database
DATABASE_URL=your_database_url_here

# Firebase
FIREBASE_CREDENTIALS_PATH=/etc/secrets/firebase-credentials.json
# Or provide the JSON directly:
FIREBASE_CREDENTIALS={"type":"service_account",...}

# Google AI
GOOGLE_API_KEY=your_google_api_key_here

# JWT Security
JWT_SECRET_KEY=your_random_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Config
APP_NAME=LegalHub API
APP_VERSION=1.0.0
DEBUG=false
DEV_MODE=false
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Optional: If you have a separate AI service
AI_SERVICE_URL=https://your-ai-service.com
```

---

## Step 4: Deploy! 🚀

1. Click "Create Web Service"
2. Wait 5-10 minutes for first build
3. Check the logs for:
   ```
   ✓ AI/RAG features disabled - missing dependencies
   Firebase initialized
   Starting LegalHub API v1.0.0
   ```

---

## Step 5: Verify Deployment

### Test Health Check:
```bash
curl https://your-app-name.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "app": "LegalHub API",
  "version": "1.0.0",
  "features": {
    "authentication": true,
    "bookings": true,
    "cases": true,
    "ai_rag": false  // This is normal!
  }
}
```

### Test API Docs:
Open in browser:
```
https://your-app-name.onrender.com/docs
```

You should see the FastAPI Swagger UI! 🎉

---

## What Works Now? ✅

- ✅ User authentication (JWT)
- ✅ Lawyer profiles and bookings
- ✅ Case reporting and management
- ✅ Chat messaging
- ✅ Analytics
- ✅ Firebase integration
- ❌ AI chatbot (disabled for now)

---

## Common Issues & Solutions

### Issue 1: "Build failed - out of memory"
**Solution:** Make sure you merged the PR and Render is using `requirements-production.txt`

Check your build logs for:
```
pip install --no-cache-dir -r requirements-production.txt
```

### Issue 2: "Module not found: langchain"
**Solution:** This is expected! AI features are disabled. If you see this error but the app still crashes:

1. Check if any code is importing AI modules without try-except
2. The updated `main.py` should handle this

### Issue 3: "Firebase credentials not found"
**Solution:** Add `FIREBASE_CREDENTIALS` environment variable in Render

Either:
- Set `FIREBASE_CREDENTIALS_PATH` to your mounted secrets path
- Or paste the entire JSON as `FIREBASE_CREDENTIALS` variable

### Issue 4: "Port already in use"
**Solution:** Make sure start command uses `$PORT` (Render provides this):
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Need AI Features?

You have 3 options:

### Option 1: Separate AI Service (Recommended)
Deploy AI features on a different platform:
- **Railway** (~$5-10/month, better ML support)
- **Modal** (serverless, pay per use)
- **Hugging Face Spaces** (free GPU inference)

Then connect via API calls from your main app.

### Option 2: Upgrade Render Plan
Upgrade to Render Pro ($25/month) for more memory, then:
1. Edit `render.yaml`
2. Uncomment the AI installation line:
   ```yaml
   pip install --no-cache-dir -r requirements-ai.txt
   ```
3. Redeploy

### Option 3: Use Managed Services
Replace self-hosted AI with managed services:
- **Pinecone** for vector database
- **OpenAI API** for embeddings
- **LangChain Cloud** for orchestration

---

## Monitoring Your App

### Check Logs:
Render Dashboard → Your Service → Logs

### Check Metrics:
Render Dashboard → Your Service → Metrics

### Set Up Alerts:
1. Go to Settings
2. Add notification emails
3. Set up health check alerts

---

## Next Steps After Deployment

1. **Test all endpoints** using the `/docs` interface
2. **Set up monitoring** (Sentry, LogRocket, etc.)
3. **Configure custom domain** (if needed)
4. **Set up CI/CD** for auto-deployment
5. **Add AI features** when ready (see options above)

---

## Getting Help

If you're still having issues:

1. **Check Render Logs** - Most errors show up there
2. **Check GitHub Issues** - Open an issue with logs
3. **Render Community** - https://community.render.com
4. **Read Full Guide** - See `DEPLOYMENT_GUIDE.md`

---

## Success Checklist

- [ ] PR merged to main
- [ ] Render service created
- [ ] Environment variables added
- [ ] Build completed successfully
- [ ] Health check returns 200 OK
- [ ] API docs accessible at `/docs`
- [ ] Can create users and authenticate
- [ ] Frontend can connect to API

If all checked, you're good to go! 🎉

---

**Last Updated:** December 2024  
**Questions?** Open an issue on GitHub