import os, json, re, httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI SERP Recommender")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_KEY = os.getenv("GROQ_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

class QueryRequest(BaseModel):
    query: str

@app.post("/api/recommend")
async def get_serpe_results(req: QueryRequest):
    if not GROQ_KEY or not TAVILY_KEY:
        raise HTTPException(500, "Missing API keys in .env")

    # 1️⃣ Fetch live web results
    async with httpx.AsyncClient() as client:
        tavily_res = await client.post("https://api.tavily.com/search", json={
            "api_key": TAVILY_KEY,
            "query": req.query,
            "max_results": 6,
            "search_depth": "basic",
            "include_answer": False
        })
    if tavily_res.status_code != 200:
        raise HTTPException(502, f"Tavily search failed: {tavily_res.text}")

    search_results = tavily_res.json()["results"]

    # 2️⃣ AI ranks & explains matches
    prompt = f"""You are an AI product/search recommender. Based on these results for "{req.query}", pick the top 3 most relevant.
Return ONLY a valid JSON array. No markdown, no explanations. Format:
[{{"title": "...", "url": "...", "snippet": "...", "reason": "1 sentence why this matches"}}]

Results: {json.dumps(search_results, ensure_ascii=False)}"""

    async with httpx.AsyncClient() as client:
        groq_res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Return ONLY valid JSON. Never use markdown."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        })

    if groq_res.status_code != 200:
        raise HTTPException(502, f"Groq AI failed: {groq_res.text}")

    data = groq_res.json()
    raw = data["choices"][0]["message"]["content"]
    print(f"🤖 Raw AI Output: {raw}")

    # Robust JSON extraction
    parsed = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        clean = raw.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r'\[[\s\S]*?\]', raw)
            if not match:
                raise HTTPException(500, f"AI failed to return JSON. Output: {raw[:100]}")
            parsed = json.loads(match.group())

    if isinstance(parsed, dict):
        parsed = parsed.get("results") or parsed.get("items") or parsed.get("recommendations") or []

    if not isinstance(parsed, list):
        parsed = []

    final_results = []
    for item in parsed[:3]:
        if not isinstance(item, dict): continue
        final_results.append({
            "title": str(item.get("title", "No Title")),
            "url": str(item.get("url", item.get("link", "#"))),
            "snippet": str(item.get("snippet", item.get("content", "")))[:180],
            "reason": str(item.get("reason", "AI matched this to your query."))
        })

    return final_results
