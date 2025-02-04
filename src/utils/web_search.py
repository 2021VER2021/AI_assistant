import hashlib
import json
from typing import List, Dict
from duckduckgo_search import DDGS
from datetime import datetime, timedelta
from database.db import get_db
from database.models import WebCache

class WebSearcher:
    ALLOWED_DOMAINS = ['arxiv.org', 'wikipedia.org']
    
    def __init__(self):
        self.ddgs = DDGS()
        self.cache_duration = timedelta(hours=24)  # Cache results for 24 hours

    def _generate_query_hash(self, query: str) -> str:
        """Generate a hash for the search query."""
        return hashlib.sha256(query.encode()).hexdigest()

    def _get_cached_results(self, query_hash: str) -> List[Dict] | None:
        """Get cached search results if they exist and are not expired."""
        with get_db() as db:
            cache_entry = db.query(WebCache).filter(WebCache.query_hash == query_hash).first()
            
            if cache_entry:
                cached_at = cache_entry.cached_at
                if datetime.utcnow() - cached_at < self.cache_duration:
                    return json.loads(cache_entry.results)
                
                # Remove expired cache entry
                db.delete(cache_entry)
                db.commit()
            
            return None

    def _cache_results(self, query_hash: str, results: List[Dict]):
        """Cache search results."""
        with get_db() as db:
            cache_entry = WebCache(
                query_hash=query_hash,
                results=json.dumps(results)
            )
            db.add(cache_entry)
            db.commit()

    def search(self, query: str, max_results: int = 2) -> List[Dict]:
        """
        Perform a web search using DuckDuckGo.
        Returns list of dicts with keys: title, link, snippet
        """
        query_hash = self._generate_query_hash(query)
        
        # Check cache first
        cached_results = self._get_cached_results(query_hash)
        if cached_results:
            return cached_results[:max_results]

        # Perform new search
        results = []
        try:
            # Get more results initially since we'll filter by domain
            search_results = list(self.ddgs.text(query, max_results=max_results))
            
            # Filter and process results
            for r in search_results:
                try:
                    # Extract domain from the URL
                    url = r.get('link', '')
                    #if not any(domain in url.lower() for domain in self.ALLOWED_DOMAINS):
                    #    continue
                        
                    results.append({
                        'title': r.get('title', 'No title'),
                        'link': url,
                        'snippet': r.get('body', 'No description available'),
                        'source': url.lower()
                    })
                    
                    if len(results) >= max_results:
                        break
                except (KeyError, AttributeError) as e:
                    print(f"Error processing search result: {e}")
                    continue
            
            # Cache results
            if results:
                self._cache_results(query_hash, results)
            
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def format_results(self, results: List[Dict]) -> str:
        """Format search results into a readable string."""
        if not results:
            print("!")
            return "No search results found from arxiv.org or wikipedia.org."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result['title']}")
            formatted.append(f"   {result['snippet']}")
            formatted.append(f"   Source: {result['source']} - {result['link']}\n")
            print(f"   Source: {result['link']}\n")
        return "\n".join(formatted)
