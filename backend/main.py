import os
import json
import re
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # Pydantic v1 compatible
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI SERP Recommender")

# CORS: Allow Vercel + localhost
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    os.getenv("VERCEL_URL", "https://your-app.vercel.app").replace("https://", "https://").replace("http://", "https://"),
]
# Add your actual Vercel URL manually if needed:
# ALLOWED_ORIGINS.append("https://your-actual-vercel-app.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load keys with clear error messages
GROQ_KEY = os.getenv("GROQ_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_KEY or not TAVILY_KEY:
    print("❌ ERROR: Missing API keys. Set GROQ_API_KEY and TAVILY_API_KEY in Render dashboard.")
    # Don't crash on import; let the endpoint handle missing keys

PRODUCTS = [
    {"id": 1, "name": "iPhone 13", "category": "Phone", "price": 499, "desc": "Reliable iOS smartphone"},
    {"id": 2, "name": "Samsung Galaxy S21", "category": "Phone", "price": 550, "desc": "Android flagship"},
    {"id": 3, "name": "MacBook Air M1", "category": "Laptop", "price": 799, "desc": "Ultra-light Apple laptop"},
    {"id": 4, "name": "Dell XPS 13", "category": "Laptop", "price": 899, "desc": "Premium Windows ultrabook"},
    {"id": 5, "name": "Sony WH-1000XM5", "category": "Headphones", "price": 349, "desc": "Noise cancellation"},
    {"id": 6, "name": "Apple AirPods Pro", "category": "Headphones", "price": 249, "desc": "Compact wireless earbuds"},
]

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health():
    return {"status": "ok", "keys_loaded": bool(GROQ_KEY and TAVILY_KEY)}

@app.post("/api/recommend")
async def get_recommendations(req: QueryRequest):
    if not GROQ_KEY or not TAVILY_KEY:
        raise HTTPException(500, detail="API keys not configured. Check Render environment variables.")

    try:
        # 1. Tavily Search
        async with httpx.AsyncClient(timeout=30.0) as client:
            tavily_resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_KEY,
                    "query": req.query,
                    "max_results": 5,
                    "search_depth": "basic"
                }
            )
        if tavily_resp.status_code != 200:
            raise Exception(f"Tavily error: {tavily_resp.text}")
        
        search_results = tavily_resp.json().get("results", [])

        # 2. Groq AI Ranking
        prompt = f"""Return ONLY a JSON array of top 3 results for "{req.query}".
Format: [{{"title":"...", "url":"...", "snippet":"...", "reason":"..."}}]
Results: {json.dumps(search_results)}"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            groq_resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "Return ONLY valid JSON array. No markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1
                }
            )
        
        if groq_resp.status_code != 200:
            raise Exception(f"Groq error: {groq_resp.text}")
        
        data = groq_resp.json()
        raw = data["choices"][0]["message"]["content"]
        
        # Parse JSON robustly
        try:
            parsed = json.loads(raw)
        except:
            clean = raw.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\[.*\]', clean, re.DOTALL)
            parsed = json.loads(match.group()) if match else []
        
        # Normalize & return
        if isinstance(parsed, dict):
            parsed = parsed.get("results") or parsed.get("items") or []
        
        results = []
        for item in (parsed or [])[:3]:
            if not isinstance(item, dict): continue
            results.append({
                "title": str(item.get("title", "No Title"))[:100],
                "url": str(item.get("url", item.get("link", "#"))),
                "snippet": str(item.get("snippet", item.get("content", "")))[:200],
                "reason": str(item.get("reason", "AI matched this query."))
            })
        
        return results

    except Exception as e:
        print(f"❌ Backend Error: {str(e)}")
        raise HTTPException(502, detail=f"Processing failed: {str(e)}")
