"""Hybrid web + Wikipedia search agent."""

import requests
import wikipediaapi
from langchain_core.tools import ToolException
from langchain_tavily import TavilySearch

from config import MAX_SEARCH_RESULTS, TAVILY_API_KEY


class SearchAgent:
    """Searches Tavily and Wikipedia in parallel for each query."""

    WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
    WIKI_USER_AGENT = "MultiAgentResearch/1.0 (research-assistant)"

    def __init__(self) -> None:
        self._tavily = None

    def _get_tavily(self) -> TavilySearch | None:
        if not TAVILY_API_KEY:
            return None
        try:
            if self._tavily is None:
                self._tavily = TavilySearch(
                    max_results=MAX_SEARCH_RESULTS,
                    tavily_api_key=TAVILY_API_KEY,
                )
            return self._tavily
        except Exception:
            return None

    @staticmethod
    def _normalize_tavily_items(raw) -> list[dict]:
        """Map Tavily API payload to {title, url, content} (same shape as before)."""
        if isinstance(raw, dict):
            items = raw.get("results", [])
        elif isinstance(raw, list):
            items = raw
        else:
            return []
        results = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", item.get("snippet", "")),
                }
            )
        return results

    def search_tavily(self, query: str) -> list[dict]:
        """Search Tavily and return normalized result dicts."""
        try:
            tavily = self._get_tavily()
            if tavily is None:
                return []
            try:
                raw = tavily.invoke({"query": query})
            except TypeError:
                raw = tavily.invoke(query)
            return self._normalize_tavily_items(raw)
        except ToolException:
            return []
        except Exception:
            return []

    def _wiki_page_titles(self, query: str, limit: int = 2) -> list[str]:
        """Resolve top Wikipedia page titles via MediaWiki opensearch."""
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "format": "json",
        }
        response = requests.get(
            self.WIKI_SEARCH_URL,
            params=params,
            headers={"User-Agent": self.WIKI_USER_AGENT},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if len(data) < 2 or not data[1]:
            return []
        return list(data[1][:limit])

    def search_wikipedia(self, query: str) -> list[dict]:
        """Search Wikipedia and return top 2 page summaries."""
        try:
            wiki = wikipediaapi.Wikipedia(
                user_agent=self.WIKI_USER_AGENT,
                language="en",
            )
            titles = self._wiki_page_titles(query, limit=2)
            results = []
            for title in titles:
                page = wiki.page(title)
                if not page.exists():
                    continue
                url = (
                    "https://en.wikipedia.org/wiki/"
                    + page.title.replace(" ", "_")
                )
                summary = page.summary or ""
                if len(summary) > 2000:
                    summary = summary[:2000] + "..."
                results.append(
                    {
                        "title": page.title,
                        "url": url,
                        "content": summary,
                    }
                )
            return results
        except Exception:
            return []

    def search(self, query: str) -> list[dict]:
        """Hybrid search: Tavily first, then Wikipedia, deduplicated by URL."""
        try:
            tavily_results = self.search_tavily(query)
            wiki_results = self.search_wikipedia(query)
            seen_urls: set[str] = set()
            combined: list[dict] = []
            for item in tavily_results + wiki_results:
                url = (item.get("url") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                combined.append(item)
            return combined
        except Exception:
            return []
