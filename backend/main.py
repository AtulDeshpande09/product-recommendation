import os
import json
import re
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI SERP Recommender")

# CORS: Allow localhost + your Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "product-recommendation-six.vercel.app",  
        "*"  # Temporary for demo - remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_KEY = os.getenv("GROQ_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

# Fallback product catalog (guarantees results if APIs fail)
PRODUCTS = [
    {"id": 1, "name": "iPhone 13", "category": "Phone", "price": 499, "desc": "Reliable iOS smartphone with great camera"},
    {"id": 2, "name": "Samsung Galaxy S21", "category": "Phone", "price": 550, "desc": "Android flagship with OLED display"},
    {"id": 3, "name": "MacBook Air M1", "category": "Laptop", "price": 799, "desc": "Ultra-light Apple laptop, all-day battery"},
    {"id": 4, "name": "Dell XPS 13", "category": "Laptop", "price": 899, "desc": "Premium Windows ultrabook"},
    {"id": 5, "name": "Sony WH-1000XM5", "category": "Headphones", "price": 349, "desc": "Industry-leading noise cancellation"},
    {"id": 6, "name": "Apple AirPods Pro", "category": "Headphones", "price": 249, "desc": "Compact wireless earbuds with ANC"},
]

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health():
    return {"status": "ok", "keys_loaded": bool(GROQ_KEY and TAVILY_KEY)}

@app.post("/api/recommend")
async def get_recommendations(req: QueryRequest):
    # 🛡️ Always build fallback results first (guarantees UX)
    fallback = []
    price_match = re.search(r'\d+', req.query)
    max_price = int(price_match.group()) if price_match else float('inf')
    
    for p in PRODUCTS:
        if req.query.lower() in p["category"].lower() or req.query.lower() in p["name"].lower():
            if p["price"] <= max_price:
                fallback.append({
                    "title": p["name"],
                    "url": f"#product-{p['id']}",
                    "snippet": p["desc"],
                    "reason": f"Matched '{p['category']}' under ${max_price}"
                })

    # 🤖 Try AI enhancement (optional - won't crash if keys/APIs fail)
    if GROQ_KEY and TAVILY_KEY:
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                # 1. Tavily Search
                tavily_resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": TAVILY_KEY,
                        "query": req.query,
                        "max_results": 6,
                        "search_depth": "basic",
                        "include_answer": False
                    }
                )
                if tavily_resp.status_code != 200:
                    raise Exception(f"Tavily error: {tavily_resp.text}")
                
                search_results = tavily_resp.json().get("results", [])

                # 2. Groq AI Ranking
                prompt = f"""You are an AI product recommender. Based on these results for "{req.query}", pick the top 3 most relevant.
Return ONLY a valid JSON array. No markdown, no explanations. Format:
[{{"title": "...", "url": "...", "snippet": "...", "reason": "1 sentence why this matches"}}]

Results: {json.dumps(search_results, ensure_ascii=False)}"""

                groq_resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        #"model": "tool-calling-model",
                        "messages": [
                            {"role": "system", "content": "Return ONLY valid JSON. Never use markdown."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1
                    }
                )
                
                if groq_resp.status_code != 200:
                    raise Exception(f"Groq error: {groq_resp.text}")

                data = groq_resp.json()
                raw = data["choices"][0]["message"]["content"]
                print(f"🤖 Raw AI Output: {raw}")

                # Robust JSON extraction
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    clean = raw.replace("```json", "").replace("```", "").strip()
                    try:
                        parsed = json.loads(clean)
                    except json.JSONDecodeError:
                        match = re.search(r'\[[\s\S]*?\]', raw)
                        if not match:
                            raise Exception(f"AI failed to return JSON: {raw[:100]}")
                        parsed = json.loads(match.group())

                # Handle object wrapper: {"results": [...]}
                if isinstance(parsed, dict):
                    parsed = parsed.get("results") or parsed.get("items") or parsed.get("recommendations") or []

                if isinstance(parsed, list) and len(parsed) > 0:
                    final_results = []
                    for item in parsed[:3]:
                        if not isinstance(item, dict): continue
                        final_results.append({
                            "title": str(item.get("title", "No Title"))[:100],
                            "url": str(item.get("url", item.get("link", "#"))),
                            "snippet": str(item.get("snippet", item.get("content", "")))[:200],
                            "reason": str(item.get("reason", "AI matched this query."))
                        })
                    return final_results

        except Exception as e:
            print(f"⚠️ AI fallback triggered: {e}")
            # Continue to return fallback results
    
    # Return fallback if AI fails or returns empty
    return fallback[:3]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
