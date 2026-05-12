import os, json, re, httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173",
    "https://product-recommendation-six.vercel.app/" 
])

GROQ_KEY = os.getenv("GROQ_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

# Static fallback catalog (guarantees results even if APIs fail)
PRODUCTS = [
    {"id": 1, "name": "iPhone 13", "category": "Phone", "price": 499, "desc": "Reliable iOS smartphone"},
    {"id": 2, "name": "Samsung Galaxy S21", "category": "Phone", "price": 550, "desc": "Android flagship"},
    {"id": 3, "name": "MacBook Air M1", "category": "Laptop", "price": 799, "desc": "Ultra-light Apple laptop"},
    {"id": 4, "name": "Dell XPS 13", "category": "Laptop", "price": 899, "desc": "Premium Windows ultrabook"},
    {"id": 5, "name": "Sony WH-1000XM5", "category": "Headphones", "price": 349, "desc": "Noise cancellation"},
    {"id": 6, "name": "Apple AirPods Pro", "category": "Headphones", "price": 249, "desc": "Compact wireless earbuds"},
]

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "keys_loaded": bool(GROQ_KEY and TAVILY_KEY)
    })

@app.route("/api/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify([])

        # 🛡️ Fallback: Simple keyword + price filter (always works)
        fallback = []
        price_match = re.search(r'\d+', query)
        max_price = int(price_match.group()) if price_match else float('inf')
        
        for p in PRODUCTS:
            if query.lower() in p["category"].lower() or query.lower() in p["name"].lower():
                if p["price"] <= max_price:
                    fallback.append({
                        "title": p["name"],
                        "url": f"#product-{p['id']}",
                        "snippet": p["desc"],
                        "reason": f"Matched category/price (fallback)"
                    })

        # 🤖 Try AI enhancement (optional - won't crash if keys missing)
        if GROQ_KEY and TAVILY_KEY:
            try:
                # 1. Tavily Search
                async with httpx.AsyncClient(timeout=20) as client:
                    tavily = await client.post("https://api.tavily.com/search", json={
                        "api_key": TAVILY_KEY,
                        "query": query,
                        "max_results": 3
                    })
                if tavily.status_code == 200:
                    results = tavily.json().get("results", [])
                    # 2. Groq AI Summary
                    async with httpx.AsyncClient(timeout=20) as client:
                        groq = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={
                            "Authorization": f"Bearer {GROQ_KEY}",
                            "Content-Type": "application/json"
                        }, json={
                            "model": "llama-3.1-8b-instant",
                            "messages": [{"role": "user", "content": f"Summarize these for '{query}' in 3 bullet points: {results}"}],
                            "temperature": 0.1
                        })
                    if groq.status_code == 200:
                        summary = groq.json()["choices"][0]["message"]["content"]
                        return jsonify([{
                            "title": "🌐 Live Web Results",
                            "url": f"https://tavily.com/search?q={query}",
                            "snippet": summary[:250],
                            "reason": "AI-curated from live web"
                        }] + fallback[:2])
            except:
                pass  # Silently fall back to static results

        return jsonify(fallback[:3])

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify([]), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
