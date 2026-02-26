"""Search tool for agents to use."""

from ..base import Tool, ToolParameter
from typing import Any, Iterable
import os

try:
    from tavily import TavilyClient
except Exception:
    TavilyClient = None

try:
    from serpapi import GoogleSearch
except Exception:
    GoogleSearch = None

CHARS_PER_TOKEN = 4  # Average Number of characters per token
DEFAULT_MAX_RESULTS = 5
SUPPORTED_RETURN_MODES = {"text", "structured", "json", "dict"}
SUPPORTED_BACKENDS = {
    "hybrid",
    "tavily",
    "serpapi",
}


# --- Static Methods ---
def _limit_text(text: str, token_limit: int) -> str:
    char_limit = token_limit * CHARS_PER_TOKEN
    if len(text) <= char_limit:
        return text
    return text[:char_limit] + "... [truncated]"


def _normalized_result(
    *,
    title: str,
    url: str,
    content: str,
    raw_content: str | None,
) -> dict[str, str]:
    payload: dict[str, str] = {
        "title": title or url,
        "url": url,
        "content": content or "",
    }
    if raw_content is not None:
        payload["raw_content"] = raw_content
    return payload


def _structured_payload(
    results: Iterable[dict[str, Any]],
    *,
    backend: str,
    answer: str | None = None,
    notices: Iterable[str] | None = None,
) -> dict[str, Any]:
    return {
        "results": list(results),
        "backend": backend,
        "answer": answer,
        "notices": list(notices or []),
    }


class SearchTool(Tool):
    """
    Hybrid search:
    1. Tavily Api - Professional AI search
    2. SerpApi - Google Search
    """

    def __init__(
        self,
        backend: str = "hybrid",
        tavily_api_key: str = None,
        serpapi_api_key: str = None,
    ):
        super().__init__(
            name="search",
            description="Search for information on the internet using a search engine.",
        )
        self.backend = backend
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.serpapi_api_key = serpapi_api_key or os.getenv("SERPAPI_API_KEY")

        # Tavily must be initialized with a client first; the client may cache the API key and connection settings, so it’s stored and reused.
        self.tavily_client = None
        self.available_backends: list[str] = []
        self._setup_backends()

    # --- Public Methods ---
    def run(self, parameters: dict[str, Any]) -> str | dict[str, Any]:
        query = (parameters.get("query") or parameters.get("input") or "").strip()
        if not query:
            return "Error: No search query provided."

        backend = str(parameters.get("backend", self.backend) or "hybrid").lower()
        backend = backend if backend in SUPPORTED_BACKENDS else self.backend

        mode = str(
            parameters.get("mode") or parameters.get("return_mode") or "text"
        ).lower()
        if mode not in SUPPORTED_RETURN_MODES:
            mode = "text"
        fetch_full_page = bool(parameters.get("fetch_full_page", False))
        max_results = int(parameters.get("max_results", DEFAULT_MAX_RESULTS))
        max_tokens = int(parameters.get("max_tokens_per_source", 2000))

        payload = self._structured_search(
            query=query,
            backend=backend,
            fetch_full_page=fetch_full_page,
            max_results=max_results,
            max_tokens=max_tokens,
        )

        if mode in {"structured", "dict", "json"}:
            return payload
        
        return self._format_text_response(query=query, payload=payload)

    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="str",
                description="The search query to use.",
                required=True,
            ),
        ]

    # --- Internal Methods ---
    def _setup_backends(self) -> None:
        if self.tavily_api_key and TavilyClient is not None:
            try:
                self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
                self.available_backends.append("tavily")
                print("✅ Tavily API is available for search.")
            except Exception as e:
                print(f"⚠️ Failed to initialize Tavily API: {e}")

        if self.serpapi_api_key and GoogleSearch is not None:
            try:
                self.available_backends.append("serpapi")
                print("✅ SerpApi is available for search.")
            except Exception as e:
                print(f"⚠️ Failed to initialize SerpApi: {e}")

        if self.backend not in SUPPORTED_BACKENDS:
            print(
                f"⚠️ Unsupported backend '{self.backend}' specified. Defaulting to 'hybrid'."
            )
            self.backend = "hybrid"
        elif self.backend == "tavily" and "tavily" not in self.available_backends:
            print(
                "⚠️ Tavily backend selected but not available. Defaulting to 'hybrid'."
            )
            self.backend = "hybrid"
        elif self.backend == "serpapi" and "serpapi" not in self.available_backends:
            print(
                "⚠️ SerpApi backend selected but not available. Defaulting to 'hybrid'."
            )
            self.backend = "hybrid"

        if self.backend == "hybrid":
            if self.available_backends:
                print(
                    f"🔀 Hybrid search will use the following backends: {', '.join(self.available_backends)}"
                )
            else:
                print(
                    "⚠️ No search backends are available. Search tool will not function properly."
                )

    def _structured_search(
        self,
        *,
        query: str,
        backend: str,
        fetch_full_page: bool,
        max_results: int,
        max_tokens: int,
    ) -> dict[str, Any]:
        if backend == "tavily":
            return self._search_tavily(
                query=query,
                fetch_full_page=fetch_full_page,
                max_results=max_results,
                max_tokens=max_tokens,
            )
        if backend == "serpapi":
            return self._search_serpapi(
                query=query,
                fetch_full_page=fetch_full_page,
                max_results=max_results,
                max_tokens=max_tokens,
            )
        if backend == "hybrid":
            return self._search_hybrid(
                query=query,
                fetch_full_page=fetch_full_page,
                max_results=max_results,
                max_tokens=max_tokens,
            )
        raise ValueError(f"Unsupported backend: '{backend}'")

    def _search_tavily(
        self,
        query: str,
        fetch_full_page: bool,
        max_results: int,
        max_tokens: int,
    ) -> dict[str, Any]:
        if not self.tavily_client:
            raise RuntimeError(
                "TAVILY_API_KEY is not set or tavily library is not installed."
            )

        response = self.tavily_client.search(
            query=query,
            max_results=max_results,
            include_raw_content=fetch_full_page,
        )
        results = []
        for item in response.get("results", [])[:max_results]:
            raw = item.get("raw_content") if fetch_full_page else item.get("content")
            if raw and fetch_full_page:
                raw = _limit_text(raw, max_tokens)
            results.append(
                _normalized_result(
                    title=item.get("title") or item.get("url", ""),
                    url=item.get("url", ""),
                    content=item.get("content") or "",
                    raw_content=raw,
                )
            )

        return _structured_payload(
            results,
            backend="tavily",
            answer=response.get("answer"),
        )

    def _search_serpapi(
        self,
        query: str,
        fetch_full_page: bool,
        max_results: int,
        max_tokens: int,
    ) -> dict[str, Any]:
        if not self.serpapi_api_key:
            raise RuntimeError("serpapi_api_key is not set.")
        if GoogleSearch is None:
            raise RuntimeError("SerpApi library is not installed.")

        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_api_key,
            # "gl": "cn",
            "hl": "en",
            "num": max_results,
        }

        # SerpApi is called directly via the class each time”
        response = GoogleSearch(params).get_dict()
        answer_box = response.get("answer_box") or {}
        answer = answer_box.get("answer") or answer_box.get("snippet")

        results = []
        for item in response.get("organic_results", [])[:max_results]:
            raw_content = item.get("snippet")
            if raw_content and fetch_full_page:
                raw_content = _limit_text(raw_content, max_tokens)
            results.append(
                _normalized_result(
                    title=item.get("title") or item.get("link", ""),
                    url=item.get("link", ""),
                    content=item.get("snippet") or "",
                    raw_content=raw_content,
                )
            )

        return _structured_payload(results, backend="serpapi", answer=answer)

    def _search_hybrid(
        self,
        *,
        query: str,
        fetch_full_page: bool,
        max_results: int,
        max_tokens: int,
    ) -> dict[str, Any]:
        notices: list[str] = []
        aggregated: list[dict[str, Any]] = []
        answer: str | None = None
        backend_used = "hybrid"

        if self.tavily_client:
            try:
                tavily_payload = self._search_tavily(
                    query=query,
                    fetch_full_page=fetch_full_page,
                    max_results=max_results,
                    max_tokens=max_tokens,
                )
                if tavily_payload["results"]:
                    return tavily_payload
                notices.append("⚠️ Tavily returned no valid results; trying other search sources")
            except Exception as exc: 
                notices.append(f"⚠️ Tavily search failed: {exc}")

        if self.serpapi_api_key and GoogleSearch is not None:
            try:
                serp_payload = self._search_serpapi(
                    query=query,
                    fetch_full_page=fetch_full_page,
                    max_results=max_results,
                    max_tokens=max_tokens,
                )
                if serp_payload["results"]:
                    serp_payload["notices"] = notices + serp_payload.get("notices", [])
                    return serp_payload
                notices.append("⚠️ SerpApi returned no valid results; trying other search sources")
            except Exception as exc: 
                notices.append(f"⚠️ SerpApi search failed: {exc}")

        return _structured_payload(
            aggregated,
            backend=backend_used,
            answer=answer,
            notices=notices,
        )
    
    def _format_text_response(self, *, query: str, payload: dict[str, Any]) -> str:
        answer = payload.get("answer")
        notices = payload.get("notices") or []
        results = payload.get("results") or []
        backend = payload.get("backend", self.backend)

        lines = [f"🔍 Search query: {query}", f"🧭 Search API: {backend}"]
        if answer:
            lines.append(f"💡 Direct Answer: {answer}")

        if results:
            lines.append("")
            lines.append("📚 Reference:")
            for idx, item in enumerate(results, start=1):
                title = item.get("title") or item.get("url", "")
                lines.append(f"[{idx}] {title}")
                if item.get("content"):
                    lines.append(f"    {item['content']}")
                if item.get("url"):
                    lines.append(f"    Source: {item['url']}")
                lines.append("")
        else:
            lines.append("❌ No relevant search results found.")

        if notices:
            lines.append("⚠️ Notices:")
            for notice in notices:
                if notice:
                    lines.append(f"- {notice}")

        return "\n".join(line for line in lines if line is not None)

# --- Quick Run ---
def search(query: str, backend: str = "hybrid") -> str:
    tool = SearchTool(backend=backend)
    return tool.run({"input": query, "backend": backend})  


def search_tavily(query: str) -> str:
    tool = SearchTool(backend="tavily")
    return tool.run({"input": query, "backend": "tavily"}) 


def search_serpapi(query: str) -> str:
    tool = SearchTool(backend="serpapi")
    return tool.run({"input": query, "backend": "serpapi"})  

def search_hybrid(query: str) -> str:
    tool = SearchTool(backend="hybrid")
    return tool.run({"input": query, "backend": "hybrid"}) 