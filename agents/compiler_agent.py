"""Report compiler agent using Gemini Pro for final report quality."""

from config import GOOGLE_API_KEY, PRO_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.llm_content import message_content_to_str
from utils.prompt_templates import COMPILER_PROMPT


class CompilerAgent:
    """Compiles structured markdown research reports with gemini-1.5-pro."""

    def __init__(self) -> None:
        self._llm = None

    def _get_llm(self) -> ChatGoogleGenerativeAI | None:
        if not GOOGLE_API_KEY:
            return None
        try:
            if self._llm is None:
                self._llm = ChatGoogleGenerativeAI(
                    model=PRO_MODEL,
                    google_api_key=GOOGLE_API_KEY,
                    temperature=0.4,
                )
            return self._llm
        except Exception:
            return None

    def compile_report(self, topic: str, summaries: list[str]) -> str:
        """Compile all sub-question summaries into a structured report."""
        try:
            llm = self._get_llm()
            if llm is None:
                return "Report compilation failed: Google API key not configured."
            if not summaries:
                return (
                    "## Executive Summary\n\n"
                    "No research summaries were available to compile a report.\n\n"
                    "## Key Findings\n\n"
                    "- No findings could be generated.\n\n"
                    "## Detailed Analysis\n\n"
                    "Please try again with a different topic or check API configuration.\n\n"
                    "## Sources\n\n"
                    "None."
                )
            joined = "\n\n---\n\n".join(summaries)
            prompt = COMPILER_PROMPT.format(topic=topic, summaries=joined)
            response = llm.invoke(prompt)
            content = message_content_to_str(
                getattr(response, "content", str(response))
            )
            return content.strip() if content else "Report compilation returned empty content."
        except Exception as exc:
            return f"Report compilation failed: {exc}"
