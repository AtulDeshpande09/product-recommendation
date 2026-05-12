import { useState } from 'react';
import './App.css';

export default function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResults([]);

    try {
      // ✅ UPDATE THIS URL to your deployed Render backend
      const res = await fetch('https://product-recommendation-lx37.onrender.com/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}: Server error`);
      }

      const data = await res.json();
      console.log('✅ Backend Response:', data);

      if (!Array.isArray(data)) {
        throw new Error('Unexpected response format');
      }

      setResults(data);
    } catch (err) {
      console.error('❌ Search Error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="serp-container">
      <header className="serp-header">
        <h1>🤖 AI Product Recommender</h1>
        <p>Live web search + AI ranking. Try: "phones under $500", "best headphones", "gaming laptops"</p>
      </header>

      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products, deals, or specs..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? '🔍 Searching & Analyzing...' : 'Search'}
        </button>
      </form>

      <section className="results-section">
        {loading && <div className="status-message loading">🔄 Fetching live results & AI analysis...</div>}

        {!loading && error && <div className="alert error">⚠️ {error}</div>}

        {!loading && !error && results.length === 0 && (
          <p className="status-message empty">Enter a query above to see AI-curated results.</p>
        )}

        {!loading && results.map((item, i) => (
          <article key={i} className="serp-card">
            <a
              href={item.url && item.url.startsWith('http') ? item.url : '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="serp-title"
            >
              {item.title || 'Untitled Result'}
            </a>
            <div className="serp-url">
              {item.url && item.url.startsWith('http') 
                ? new URL(item.url).hostname.replace('www.', '') 
                : 'Local Result'}
            </div>
            <p className="serp-snippet">{item.snippet || 'No description available.'}</p>
            <div className="ai-badge">🤖 AI Reason: {item.reason || 'Matched your query.'}</div>
          </article>
        ))}
      </section>

      <footer className="dev-note">
        💡 Built with React + FastAPI + Groq + Tavily. Keys secured server-side.
      </footer>
    </div>
  );
}