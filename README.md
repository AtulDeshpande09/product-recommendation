# AI Product Recommendation System

> A full-stack AI-powered product recommender with live web search, intelligent ranking, and graceful fallbacks.

🔗 **Live Demo**: [https://product-recommendation-six.vercel.app](https://product-recommendation-six.vercel.app)


https://github.com/user-attachments/assets/f25041ad-d2a8-4179-a6e4-5b15534fb82c


---

## Features

✅ **Natural Language Search**  
Users type queries like `"phones under $500"` or `"best noise cancelling headphones"` and get AI-curated results.

✅ **Live Web Search + AI Ranking**  
Powered by **Tavily** (real-time web search) + **Groq** (Llama 3.1) for intelligent result ranking and explanation.

✅ **Graceful Fallback**  
If external APIs fail or rate-limit, a deterministic client-side filter guarantees results — no broken UX.

✅ **Production-Ready Architecture**  
- React/Vite frontend (Vercel)  
- FastAPI backend (Render)  
- API keys secured server-side  
- CORS, async I/O, error handling, and logging

✅ **SERP-Style UI**  
Clean, Google-style results with title, URL, snippet, and AI-generated "why this matches" reasoning.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, CSS Modules |
| **Backend** | FastAPI, Python 3.11, Uvicorn |
| **AI/ML** | Groq (Llama 3.1-8b-instant), Tavily Search API |
| **Deployment** | Vercel (frontend), Render (backend) |
| **Dev Tools** | httpx, python-dotenv, pydantic |

---

## Architecture

```
┌─────────────────┐
│   React Frontend│
│   (Vercel)      │
└────────┬────────┘
         │ HTTPS POST /api/recommend
         ▼
┌─────────────────┐
│  FastAPI Backend│
│  (Render)       │
└────────┬────────┘
         │ Async HTTP Calls
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Tavily API    │     │   Groq API      │
│  (Web Search)   │     │ (LLM Ranking)   │
└─────────────────┘     └─────────────────┘
```

---

## Local Development Setup

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- [Groq API Key](https://console.groq.com/keys)
- [Tavily API Key](https://tavily.com)

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/ai-recommender.git
cd ai-recommender

# Frontend
cd frontend && npm install && cd ..

# Backend
cd backend && pip install -r requirements.txt && cd ..
```

### 2. Environment Variables
Create `backend/.env`:
```env
GROQ_API_KEY=gsk_your_groq_key_here
TAVILY_API_KEY=tvly_your_tavily_key_here
```

### 3. Run Locally
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open `http://localhost:5173` → search `"best headphones under $100"`

---

## Deployment Guide

### Backend (Render)
1. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Runtime**: `python-3.11.9` (via `runtime.txt`)
4. Add Environment Variables:
   ```
   GROQ_API_KEY=your_key
   TAVILY_API_KEY=your_key
   ```
5. Deploy → Copy URL: `https://your-app.onrender.com`

### Frontend (Vercel)
1. Go to [vercel.com/new](https://vercel.com/new) → Import GitHub repo
2. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Deploy → Copy URL: `https://your-app.vercel.app`

### Connect Them
1. Update `frontend/src/App.jsx` fetch URL to your Render backend
2. Update `backend/main.py` CORS `allow_origins` to include your Vercel URL
3. Redeploy both

---

## 🔌 API Documentation

### `POST /api/recommend`
**Request**
```json
{
  "query": "best wireless earbuds under $50"
}
```

**Response**
```json
[
  {
    "title": "Sony WF-C500 Truly Wireless Earbuds",
    "url": "https://example.com/product",
    "snippet": "Compact, affordable earbuds with 10-hour battery life...",
    "reason": "Matched 'wireless earbuds' under $50 with high user ratings"
  }
]
```

### `GET /health`
```json
{
  "status": "ok",
  "keys_loaded": true
}
```

---

## 🔐 Security Notes

- ✅ API keys are **never committed** to Git (use `.env` + platform env vars)
- ✅ Backend proxies all AI calls — keys stay server-side
- ✅ CORS restricts frontend access to authorized domains
- ⚠️ For production: add rate limiting, authentication, and request logging

---

## 🧪 Testing

```bash
# Test backend directly
curl -X POST https://your-app.onrender.com/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "gaming laptops under $1000"}'

# Test frontend
# Open Vercel URL → search → verify results load

# Test fallback (temporarily remove API keys)
# Should still return static product matches
```

## 📄 License

MIT License — free to use, modify, and learn from.

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) for blazing-fast LLM inference
- [Tavily](https://tavily.com) for AI-optimized web search
- [Render](https://render.com) & [Vercel](https://vercel.com) for seamless deployments
- FastAPI & React communities for excellent documentation

---
