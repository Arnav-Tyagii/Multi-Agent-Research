"""Orchestrator coordinating multi-agent parallel research pipeline."""

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from agents.compiler_agent import CompilerAgent
from agents.search_agent import SearchAgent
from agents.summary_agent import SummaryAgent
from config import FLASH_MODEL, GOOGLE_API_KEY, MAX_WORKERS
from memory.vector_store import VectorStore
from utils.prompt_templates import SEARCH_DECOMPOSE_PROMPT
from utils.llm_content import message_content_to_str
from utils.report_builder import format_report


class OrchestratorAgent:
    """Coordinates decomposition, parallel search/summarise, compile, and cache."""

    def __init__(self) -> None:
        self.search_agent = SearchAgent()
        self.summary_agent = SummaryAgent()
        self.compiler_agent = CompilerAgent()
        self.vector_store = VectorStore()
        self._decompose_llm = None

    def _get_decompose_llm(self) -> ChatGoogleGenerativeAI | None:
        if not GOOGLE_API_KEY:
            return None
        try:
            if self._decompose_llm is None:
                self._decompose_llm = ChatGoogleGenerativeAI(
                    model=FLASH_MODEL,
                    google_api_key=GOOGLE_API_KEY,
                    temperature=0.2,
                )
            return self._decompose_llm
        except Exception:
            return None

    def _parse_sub_questions(self, text: str) -> list[str]:
        sub_questions: list[str] = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^\s*\d+[\.\)]\s*(.+)", line)
            if match:
                sub_questions.append(match.group(1).strip())
            elif line and not sub_questions:
                sub_questions.append(line)
        return sub_questions[:5]

    def _decompose_topic(self, topic: str) -> list[str]:
        try:
            llm = self._get_decompose_llm()
            if llm is None:
                return [
                    f"What is {topic}?",
                    f"What are the key developments related to {topic}?",
                    f"What are the implications and future outlook for {topic}?",
                ]
            prompt = SEARCH_DECOMPOSE_PROMPT.format(topic=topic)
            response = llm.invoke(prompt)
            content = message_content_to_str(
                getattr(response, "content", str(response))
            )
            parsed = self._parse_sub_questions(content)
            if len(parsed) >= 3:
                return parsed
            return parsed or [
                f"What is {topic}?",
                f"What are the main aspects of {topic}?",
                f"What is the significance of {topic}?",
            ]
        except Exception:
            return [
                f"What is {topic}?",
                f"What are the main aspects of {topic}?",
                f"What is the significance of {topic}?",
            ]

    def _process_sub_question(self, sub_question: str, topic: str) -> tuple[str, float]:
        """Search, summarise, and cache one sub-question (thread worker)."""
        started = time.perf_counter()
        try:
            search_results = self.search_agent.search(sub_question)
            summary = self.summary_agent.summarise(topic, search_results)
            self.vector_store.store_summary(topic, sub_question, summary)
            return summary, time.perf_counter() - started
        except Exception:
            return "", time.perf_counter() - started

    def run(self, topic: str, progress_callback=None) -> tuple[str, dict[str, Any]]:
        """Execute pipeline; return (formatted report, timing metrics)."""
        topic = topic.strip()
        timing: dict[str, Any] = {
            "from_cache": False,
            "sub_questions": 0,
            "decompose_s": 0.0,
            "parallel_wall_s": 0.0,
            "sequential_equivalent_s": 0.0,
            "compile_s": 0.0,
            "total_s": 0.0,
            "speedup": 0.0,
        }
        pipeline_start = time.perf_counter()

        if not topic:
            timing["total_s"] = time.perf_counter() - pipeline_start
            return (
                format_report("Unknown", "Please provide a valid research topic."),
                timing,
            )

        cache_note = ""
        summaries: list[str] = []

        if self.vector_store.has_cached_report(topic):
            summaries = self.vector_store.get_summaries_for_topic(topic)
            timing["from_cache"] = True
            timing["sub_questions"] = len(summaries)
            cache_note = (
                "> **Note:** Report compiled from cached research summaries "
                "stored in ChromaDB.\n\n"
            )
        else:
            decompose_start = time.perf_counter()
            sub_questions = self._decompose_topic(topic)
            timing["decompose_s"] = time.perf_counter() - decompose_start
            timing["sub_questions"] = len(sub_questions)
            total = len(sub_questions)
            task_durations: list[float] = []

            parallel_start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(
                        self._process_sub_question, sq, topic
                    ): sq
                    for sq in sub_questions
                }
                for i, future in enumerate(as_completed(futures)):
                    sub_q = futures[future]
                    try:
                        summary, duration = future.result()
                        task_durations.append(duration)
                        if summary:
                            summaries.append(summary)
                        if progress_callback:
                            progress_callback(sub_q, i + 1, total)
                    except Exception:
                        continue
            timing["parallel_wall_s"] = time.perf_counter() - parallel_start
            timing["sequential_equivalent_s"] = sum(task_durations)
            if timing["parallel_wall_s"] > 0 and task_durations:
                timing["speedup"] = round(
                    timing["sequential_equivalent_s"] / timing["parallel_wall_s"],
                    1,
                )

        if not summaries:
            final_report = (
                "## Executive Summary\n\n"
                "Unable to generate research findings for this topic.\n\n"
                "## Key Findings\n\n"
                "- No sub-question summaries completed successfully.\n\n"
                "## Detailed Analysis\n\n"
                "Please verify API keys and try again.\n\n"
                "## Sources\n\n"
                "None."
            )
        else:
            compile_start = time.perf_counter()
            final_report = self.compiler_agent.compile_report(topic, summaries)
            timing["compile_s"] = time.perf_counter() - compile_start

        if cache_note:
            final_report = cache_note + final_report

        timing["total_s"] = round(time.perf_counter() - pipeline_start, 1)
        timing["parallel_wall_s"] = round(timing["parallel_wall_s"], 1)
        timing["sequential_equivalent_s"] = round(
            timing["sequential_equivalent_s"], 1
        )
        timing["decompose_s"] = round(timing["decompose_s"], 1)
        timing["compile_s"] = round(timing["compile_s"], 1)

        return format_report(topic, final_report), timing
