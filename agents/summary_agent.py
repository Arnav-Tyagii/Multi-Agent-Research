"""Summary agent using Gemini Flash for fast summarisation."""

from config import FLASH_MODEL, GOOGLE_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.llm_content import message_content_to_str
from utils.prompt_templates import SUMMARY_PROMPT


class SummaryAgent:
    """Summarises search results with gemini-1.5-flash."""

    def __init__(self) -> None:
        self._llm = None

    def _get_llm(self) -> ChatGoogleGenerativeAI | None:
        if not GOOGLE_API_KEY:
            return None
        try:
            if self._llm is None:
                self._llm = ChatGoogleGenerativeAI(
                    model=FLASH_MODEL,
                    google_api_key=GOOGLE_API_KEY,
                    temperature=0.3,
                )
            return self._llm
        except Exception:
            return None

    def _format_results(self, search_results: list[dict]) -> str:
        blocks = []
        for result in search_results:
            blocks.append(
                f"Title: {result.get('title', 'N/A')}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"Content: {result.get('content', 'N/A')}\n---"
            )
        return "\n".join(blocks)

    def summarise(self, topic: str, search_results: list[dict]) -> str:
        """Produce a concise summary with cited sources."""
        if not search_results:
            return "No results found for this sub-question."
        try:
            llm = self._get_llm()
            if llm is None:
                return "Summary unavailable: Google API key not configured."
            formatted = self._format_results(search_results)
            prompt = SUMMARY_PROMPT.format(topic=topic, results=formatted)
            response = llm.invoke(prompt)
            content = message_content_to_str(
                getattr(response, "content", str(response))
            )
            return content.strip() if content else "Summary generation returned empty content."
        except Exception as exc:
            return f"Summary generation failed: {exc}"
