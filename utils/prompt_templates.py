"""Prompt template strings for agent LLM calls."""

SEARCH_DECOMPOSE_PROMPT = """Given a research topic, break it into 3-5 specific, non-overlapping \
sub-questions that together cover the topic comprehensively.
Return ONLY a numbered list, no preamble.

Research topic: {topic}"""

SUMMARY_PROMPT = """Given a research topic and raw search results (title, URL, content snippet), \
write a concise 150-200 word summary of the key findings.
Always end with a "Sources:" section listing all URLs cited.

Research topic: {topic}

Search results:
{results}"""

COMPILER_PROMPT = """Given a research topic and a list of summaries from multiple searches, \
compile a structured research report in markdown with:
- ## Executive Summary (3-4 sentences)
- ## Key Findings (bullet points, grouped by theme)
- ## Detailed Analysis (2-3 paragraphs)
- ## Sources (numbered list of all URLs cited, deduplicated)

Research topic: {topic}

Summaries:
{summaries}"""
