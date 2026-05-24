"""Streamlit frontend — Cinematic Modern AI Canvas."""

import os
import random
import re
import time
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st

from config import (
    GOOGLE_API_KEY,
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    TAVILY_API_KEY,
)
from agents.orchestrator import OrchestratorAgent

# LangSmith tracing (unchanged)
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    os.environ.setdefault("LANGCHAIN_API_KEY", LANGSMITH_API_KEY)

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _inject_cinematic_theme() -> None:
    """Glassmorphism + cinematic mesh glow — injected at app startup."""
    st.markdown(
        """
        <style>
        /* ═══ 1. CINEMATIC BACKGROUND (deep blue-black + neon mesh) ═══ */
        [data-testid="stAppViewContainer"] {
            background-color: #030712 !important;
            background-image:
                radial-gradient(circle at 50% 30%, rgba(29, 78, 216, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 0% 0%, rgba(88, 28, 135, 0.08) 0%, transparent 40%) !important;
            background-attachment: fixed !important;
            position: relative !important;
        }
        [data-testid="stAppViewContainer"] > .main {
            background: transparent !important;
        }
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            top: 18%;
            left: 50%;
            transform: translateX(-50%);
            width: min(900px, 85vw);
            height: 420px;
            background: radial-gradient(
                ellipse at center,
                rgba(59, 130, 246, 0.22) 0%,
                rgba(139, 92, 246, 0.08) 40%,
                transparent 72%
            );
            filter: blur(72px);
            pointer-events: none;
            z-index: 0;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
            background-color: transparent !important;
            color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [data-testid="stDecoration"] { display: none !important; }
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] { display: none !important; }
        .block-container {
            max-width: 880px;
            padding-top: 2rem;
            padding-bottom: 5rem;
            margin-left: auto;
            margin-right: auto;
            position: relative;
            z-index: 1;
        }
        footer { visibility: hidden; }

        /* ═══ 5. MODERN HEADER (crisp gradient — hero only) ═══ */
        .canvas-hero h1 {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                Helvetica, Arial, sans-serif !important;
            font-size: 2.1rem !important;
            letter-spacing: -0.03em !important;
            font-weight: 700 !important;
            margin: 0 !important;
            background: linear-gradient(to right, #ffffff, #9ca3af) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
        }
        .canvas-hero p {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                Helvetica, Arial, sans-serif !important;
            color: #6b7280 !important;
            font-size: 0.92rem !important;
            margin: 0.5rem 0 0 0 !important;
            letter-spacing: -0.01em;
        }

        /* ═══ 2. FROSTED GLASS — search input ═══ */
        div[data-testid="stTextInput"] label {
            font-size: 0.72rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            color: #6b7280 !important;
            font-weight: 600 !important;
        }
        div[data-testid="stTextInput"] input {
            background-color: rgba(17, 24, 39, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-radius: 10px !important;
            color: #f3f4f6 !important;
            padding: 0.95rem 1.1rem !important;
            font-size: 1.02rem !important;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: rgba(59, 130, 246, 0.6) !important;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.25) !important;
            outline: none !important;
        }

        /* ═══ 2b. FROSTED GLASS — toolbar popovers (modern, no emoji) ═══ */
        .toolbar-popover [data-testid="stPopover"] button {
            background: rgba(17, 24, 39, 0.55) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-radius: 8px !important;
            color: #d1d5db !important;
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            white-space: nowrap !important;
            padding: 0.5rem 0.95rem !important;
            min-width: 5.5rem !important;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.22s ease !important;
        }
        .toolbar-popover [data-testid="stPopover"] button:hover {
            background: rgba(255, 255, 255, 0.07) !important;
            border-color: rgba(148, 163, 184, 0.35) !important;
            color: #f9fafb !important;
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.12) !important;
        }
        .toolbar-popover [data-testid="stPopover"] button p {
            font-size: 0.72rem !important;
            letter-spacing: 0.08em !important;
        }

        /* ═══ 3. QUICK TOPIC CHIPS (glass pills) ═══ */
        .chip-row-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #4b5563;
            margin: 1rem 0 0.55rem 0;
        }
        .chip-row-block div[data-testid="column"] button {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border-radius: 20px !important;
            padding: 6px 18px !important;
            color: #9ca3af !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .chip-row-block div[data-testid="column"] button:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(59, 130, 246, 0.15) !important;
        }

        /* ═══ 4. NEON RESEARCH CTA ═══ */
        .research-cta div.stButton > button[kind="primary"],
        .research-cta [data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
            border: none !important;
            color: #ffffff !important;
            padding: 10px 28px !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em !important;
            border-radius: 8px !important;
            min-width: 10rem !important;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        .research-cta div.stButton > button[kind="primary"]:hover,
        .research-cta [data-testid="stButton"] > button[kind="primary"]:hover {
            box-shadow: 0 4px 25px rgba(139, 92, 246, 0.5) !important;
            transform: scale(1.02) !important;
        }
        .clear-cta [data-testid="stButton"] button {
            background: rgba(17, 24, 39, 0.45) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            color: #9ca3af !important;
            border-radius: 8px !important;
            transition: all 0.25s ease !important;
        }
        .clear-cta [data-testid="stButton"] button:hover {
            border-color: rgba(255, 255, 255, 0.2) !important;
            color: #f3f4f6 !important;
        }

        /* Performance pills — glass */
        .perf-dashboard {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.55rem;
            margin: 1.25rem 0 1.75rem 0;
        }
        .perf-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(8px);
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 0.82rem;
            color: #9ca3af;
            white-space: nowrap;
        }
        .perf-pill strong { color: #f9fafb; font-weight: 600; }

        /* Floating report deck — frosted panel */
        .deck-marker + div [data-testid="stMarkdownContainer"] {
            background: rgba(17, 24, 39, 0.55) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border-radius: 12px !important;
            padding: 35px !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35) !important;
            margin: 0.5rem 0 2rem 0 !important;
        }
        .deck-marker + div [data-testid="stMarkdownContainer"] h1 {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                Helvetica, Arial, sans-serif !important;
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            color: #f9fafb !important;
            -webkit-text-fill-color: #f9fafb !important;
            background: none !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 1rem;
            margin-top: 0 !important;
        }
        .deck-marker + div [data-testid="stMarkdownContainer"] h2,
        .deck-marker + div [data-testid="stMarkdownContainer"] h3 {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                Helvetica, Arial, sans-serif !important;
            letter-spacing: -0.02em !important;
            font-weight: 600 !important;
            color: #e5e7eb !important;
            -webkit-text-fill-color: #e5e7eb !important;
            background: none !important;
        }
        .deck-marker + div [data-testid="stMarkdownContainer"] h2 {
            font-size: 1.08rem !important;
            margin-top: 2rem !important;
        }
        .deck-marker + div [data-testid="stMarkdownContainer"] p,
        .deck-marker + div [data-testid="stMarkdownContainer"] li {
            color: #d1d5db !important;
            line-height: 1.8 !important;
            font-size: 0.97rem !important;
        }
        .deck-marker + div [data-testid="stMarkdownContainer"] hr {
            border: none !important;
            border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
            margin: 2rem 0 !important;
        }

        /* Bibliography cards — glass */
        .bib-heading {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #4b5563;
            margin: 2rem 0 1rem 0;
            font-weight: 600;
        }
        .source-card-wrap [data-testid="stLinkButton"] a {
            background: rgba(17, 24, 39, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 12px !important;
            padding: 0.85rem 1rem !important;
            transition: all 0.25s ease !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
        }
        .source-card-wrap [data-testid="stLinkButton"] a:hover {
            border-color: rgba(59, 130, 246, 0.45) !important;
            background: rgba(59, 130, 246, 0.1) !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 28px rgba(59, 130, 246, 0.2) !important;
        }

        /* Pipeline timeline — glass panel */
        [data-testid="stStatus"] {
            background: rgba(17, 24, 39, 0.55) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            backdrop-filter: blur(12px) !important;
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_cinematic_theme()

# --- Quick topic pool (3 random chips picked per session / on clear) ---
TOPIC_CHIP_POOL = [
    ("Quantum Computing", "Impact of quantum computing on cryptography"),
    ("CRISPR Editing", "CRISPR gene editing ethical considerations"),
    ("Superconductors", "Room-temperature superconductors and energy applications"),
    ("Renewable Energy", "Renewable energy adoption in developing nations"),
    ("LLMs in Healthcare", "Large language models in healthcare diagnostics"),
    ("Space Tourism", "Space tourism economic and environmental effects"),
    ("Geometric Deep Learning", "Geometric deep learning for 3D molecular structure prediction"),
    ("Autonomous Vehicles", "Autonomous vehicles and urban transportation planning"),
    ("Climate Tipping Points", "Climate change tipping points and ecosystem collapse risk"),
    ("Fusion Energy", "Nuclear fusion energy progress and commercial viability"),
]

# --- Session state ---
if "last_report" not in st.session_state:
    st.session_state["last_report"] = ""
if "last_timing" not in st.session_state:
    st.session_state["last_timing"] = {}
if "last_topic" not in st.session_state:
    st.session_state["last_topic"] = ""
if "history" not in st.session_state:
    st.session_state["history"] = []
if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""
if "pipeline_log" not in st.session_state:
    st.session_state["pipeline_log"] = []
if "pipeline_summary" not in st.session_state:
    st.session_state["pipeline_summary"] = ""
if "pipeline_running" not in st.session_state:
    st.session_state["pipeline_running"] = False


def _key_status(key: str) -> str:
    return "Connected" if key else "Missing"


def _tracing_status() -> str:
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "yes")
    has_key = bool(LANGSMITH_API_KEY)
    return "Active" if tracing and has_key else "Inactive"


def _strip_markdown(text: str) -> str:
    plain = re.sub(r"#{1,6}\s*", "", text)
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
    plain = re.sub(r"\*([^*]+)\*", r"\1", plain)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
    plain = re.sub(r"^[-*+]\s+", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"^>\s?", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    return plain.strip()


def _extract_urls(report: str) -> list[str]:
    urls = re.findall(r"https?://[^\s\)\]>\"']+", report)
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        url = url.rstrip(".,;)")
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def _source_card_meta(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "") or "source"
    slug = (parsed.path or "/").strip("/")[:32] or domain
    return domain, slug


def _render_perf_pills(elapsed: float, timing: dict, source_count: int, sub_count: int) -> None:
    pills: list[str] = []
    speedup = timing.get("speedup", 0)
    if speedup and speedup > 1.0 and not timing.get("from_cache"):
        pills.append(f'<span class="perf-pill">⚡ <strong>{speedup}x</strong> Parallel Speedup</span>')
    if elapsed:
        pills.append(f'<span class="perf-pill">⏱️ <strong>{elapsed:.1f}s</strong> Execution Time</span>')
    if sub_count:
        pills.append(f'<span class="perf-pill">🔬 <strong>{sub_count}</strong> Sub-agents</span>')
    if source_count:
        pills.append(f'<span class="perf-pill">📎 <strong>{source_count}</strong> Sources</span>')
    if timing.get("from_cache"):
        pills.append('<span class="perf-pill">📂 <strong>ChromaDB</strong> Cache Hit</span>')
    elif timing.get("compile_s"):
        pills.append(
            f'<span class="perf-pill">🧠 <strong>{timing.get("compile_s", 0):.1f}s</strong> Compile</span>'
        )
    if pills:
        st.markdown(
            f'<div class="perf-dashboard">{"".join(pills)}</div>',
            unsafe_allow_html=True,
        )


def _render_source_card_grid(urls: list[str]) -> None:
    if not urls:
        st.caption("No sources found in this report.")
        return
    cols_per_row = 3
    for row_start in range(0, len(urls), cols_per_row):
        cols = st.columns(cols_per_row, gap="medium")
        for col_idx, col in enumerate(cols):
            url_idx = row_start + col_idx
            if url_idx >= len(urls):
                break
            url = urls[url_idx]
            domain, slug = _source_card_meta(url)
            with col:
                st.markdown('<div class="source-card-wrap">', unsafe_allow_html=True)
                st.link_button(
                    f"**[{url_idx + 1}]** {domain}\n\n{slug}",
                    url,
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)


def _render_report_deck(markdown_report: str) -> None:
    """Floating document sheet for the compiled report."""
    st.markdown('<div class="deck-marker"></div>', unsafe_allow_html=True)
    st.markdown(markdown_report)


def _add_to_history(topic: str, report: str) -> None:
    entry = {
        "topic": topic,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report": report,
    }
    history = [h for h in st.session_state.get("history", []) if h.get("topic") != topic]
    history.insert(0, entry)
    st.session_state["history"] = history[:5]


def _refresh_active_chips() -> None:
    """Pick 3 new quick topics (new browser session or after Clear)."""
    st.session_state["active_chips"] = random.sample(
        TOPIC_CHIP_POOL, min(3, len(TOPIC_CHIP_POOL))
    )


def _ensure_active_chips() -> None:
    if "active_chips" not in st.session_state:
        _refresh_active_chips()


def _apply_chip(topic_value: str) -> None:
    """Set topic before text_input is drawn (use with on_click only)."""
    st.session_state["topic_input"] = topic_value
    st.session_state["topic_field"] = topic_value


def _load_history_report(topic: str, report: str) -> None:
    st.session_state["last_report"] = report
    st.session_state["last_topic"] = topic
    st.session_state["topic_input"] = topic
    st.session_state["topic_field"] = topic


def _render_history_popover() -> None:
    with st.popover("History"):
        history = st.session_state.get("history", [])
        if not history:
            st.caption("No reports yet.")
        else:
            for i, entry in enumerate(history):
                st.caption(entry["timestamp"])
                if st.button(
                    entry["topic"],
                    key=f"hist_{i}",
                    use_container_width=True,
                    on_click=_load_history_report,
                    args=(entry["topic"], entry["report"]),
                ):
                    pass


def _render_status_popover() -> None:
    with st.popover("Status"):
        st.markdown("**API connections**")
        st.markdown(f"Google Gemini · {_key_status(GOOGLE_API_KEY)}")
        st.markdown(f"Tavily Search · {_key_status(TAVILY_API_KEY)}")
        st.markdown(f"LangSmith · {_key_status(LANGSMITH_API_KEY)}")
        st.markdown(f"Tracing · {_tracing_status()}")
        st.caption(f"Project: `{LANGSMITH_PROJECT}`")


def _render_topic_chips() -> None:
    _ensure_active_chips()
    chips = st.session_state["active_chips"]
    st.markdown('<p class="chip-row-label">Quick topics</p>', unsafe_allow_html=True)
    st.markdown('<div class="chip-row-block">', unsafe_allow_html=True)
    cols = st.columns(len(chips), gap="small")
    for col, (label, query) in zip(cols, chips):
        with col:
            st.button(
                label,
                key=f"chip_{label}_{query[:20]}",
                use_container_width=True,
                on_click=_apply_chip,
                args=(query,),
            )
    st.markdown("</div>", unsafe_allow_html=True)


head_title, head_tools = st.columns([3, 1.4], gap="medium")
with head_title:
    st.markdown(
        """
        <div class="canvas-hero">
            <h1>Research Assistant</h1>
            <p>Parallel agents · Web & Wikipedia · Gemini · ChromaDB</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with head_tools:
    st.markdown('<div class="toolbar-popover">', unsafe_allow_html=True)
    t1, t2 = st.columns(2, gap="small")
    with t1:
        _render_history_popover()
    with t2:
        _render_status_popover()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

report_to_show = st.session_state.get("last_report", "")
showing_report = bool(report_to_show) and not st.session_state.get("pipeline_running")

# Chips must render before text_input so on_click can set topic_field safely
if not showing_report:
    _render_topic_chips()

topic = st.text_input(
    "Research topic",
    value=st.session_state.get("topic_input", ""),
    placeholder="Ask anything — agents will research, cite, and compile…",
    label_visibility="visible",
    key="topic_field",
)
st.session_state["topic_input"] = topic

# Centered glowing CTA
_, cta_center, _ = st.columns([1, 2, 1])
with cta_center:
    btn_row1, btn_row2 = st.columns([2, 1], gap="small")
    with btn_row1:
        st.markdown('<div class="research-cta">', unsafe_allow_html=True)
        generate = st.button("✦ Research", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with btn_row2:
        st.markdown('<div class="clear-cta">', unsafe_allow_html=True)
        clear_clicked = st.button("Clear", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if clear_clicked:
    st.session_state["last_report"] = ""
    st.session_state["last_timing"] = {}
    st.session_state["last_topic"] = ""
    st.session_state["topic_input"] = ""
    st.session_state["pipeline_log"] = []
    st.session_state["pipeline_summary"] = ""
    st.session_state["pipeline_running"] = False
    if "topic_field" in st.session_state:
        del st.session_state["topic_field"]
    _refresh_active_chips()
    st.rerun()

display_topic = st.session_state.get("last_topic") or topic

# ── Pipeline execution (Phase 3: timeline in st.status only) ──
if generate:
    if not topic.strip():
        st.warning("Enter a research topic to begin.")
    elif not GOOGLE_API_KEY:
        st.error("Add `GOOGLE_API_KEY` to your `.env` file.")
    else:
        st.session_state["pipeline_running"] = True
        st.session_state["pipeline_log"] = []
        orchestrator = OrchestratorAgent()
        start_time = time.time()
        sub_questions_total = [0]

        with st.status("⏳ Live workflow timeline", expanded=True) as status:
            timeline = st.empty()
            timer_slot = st.empty()

            def _paint_timeline() -> None:
                lines = st.session_state["pipeline_log"]
                if lines:
                    timeline.markdown("\n".join(f"→ {ln}" for ln in lines))

            def _update_elapsed(status_label: str | None = None) -> None:
                """Main-thread only — avoids NoSessionContext from background threads."""
                elapsed = time.time() - start_time
                timer_slot.caption(f"⏱ {elapsed:.0f}s elapsed")
                if status_label:
                    status.update(label=status_label, state="running")

            def progress_callback(sub_question: str, index: int, total: int) -> None:
                sub_questions_total[0] = total
                st.session_state["pipeline_log"].append(
                    f"[{index}/{total}] {sub_question}"
                )
                _paint_timeline()
                _update_elapsed(
                    f"Parallel agents researching ({index}/{total})"
                )

            st.session_state["pipeline_log"] = ["Decomposing topic into sub-questions…"]
            _paint_timeline()
            _update_elapsed("Decomposing topic…")

            try:
                report, timing = orchestrator.run(
                    topic.strip(), progress_callback=progress_callback
                )
                elapsed = time.time() - start_time
                sub_n = timing.get("sub_questions", sub_questions_total[0] or 3)

                st.session_state["pipeline_log"].append("Compiling report (Gemini Pro)…")
                _paint_timeline()
                timer_slot.caption(f"⏱ {elapsed:.0f}s elapsed")
                status.update(label="Compilation complete", state="complete")

                st.session_state["last_report"] = report
                st.session_state["last_topic"] = topic.strip()
                st.session_state["last_elapsed"] = elapsed
                st.session_state["last_timing"] = timing
                st.session_state["last_sub_count"] = sub_n
                st.session_state["pipeline_running"] = False
                st.session_state["pipeline_log"] = []
                st.session_state["pipeline_summary"] = ""
                _add_to_history(topic.strip(), report)
                st.rerun()
            except Exception as exc:
                status.update(label="Pipeline failed", state="error")
                st.session_state["pipeline_running"] = False
                st.error(f"Something went wrong: {exc}")

# ── Results workspace (no pipeline clutter after completion) ──
if showing_report:
    urls = _extract_urls(report_to_show)
    elapsed = st.session_state.get("last_elapsed", 0)
    timing = st.session_state.get("last_timing", {})
    sub_count = st.session_state.get("last_sub_count", 3)

    _render_perf_pills(elapsed, timing, len(urls), sub_count)
    _render_report_deck(report_to_show)

    st.markdown('<p class="bib-heading">Bibliography</p>', unsafe_allow_html=True)
    _render_source_card_grid(urls)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
    dl1, dl2, _ = st.columns([1, 1, 2])
    safe_name = re.sub(r"[^\w\-]+", "_", display_topic or "report")[:50]
    with dl1:
        st.download_button(
            "↓ Markdown",
            data=report_to_show,
            file_name=f"research_{safe_name}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "↓ Plain text",
            data=_strip_markdown(report_to_show),
            file_name=f"research_{safe_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )
