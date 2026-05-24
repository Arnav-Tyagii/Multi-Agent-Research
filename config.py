"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")

FLASH_MODEL = "gemini-3.5-flash"
PRO_MODEL = "gemini-3.5-flash"
MAX_SEARCH_RESULTS = 5
MAX_CONCURRENT_TOPICS = 10
MAX_WORKERS = 5
CHROMA_PERSIST_DIR = "./chroma_db"
LANGSMITH_PROJECT = "multi-agent-research"
