"""Report formatting utilities."""

from datetime import datetime


def format_report(topic: str, report_markdown: str) -> str:
    """Prepend title and generation timestamp to the report markdown."""
    header = f"# Research Report: {topic}\n\n"
    header += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    header += "---\n\n"
    return header + report_markdown.strip()
