"""Project configuration and paths."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
DB_PATH = DATA_DIR / "transwarp_advisor.db"
CHROMA_DIR = ROOT / ".chroma"
MCP_SERVER = ROOT / "mcp_server" / "crm_server.py"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CRM_MCP_URL = os.getenv("CRM_MCP_URL", "http://127.0.0.1:8765/mcp")

APP_NAME = "星环产品选型助手"
APP_SUBTITLE = "Transwarp Product Advisor · 产品选型与售前线索"
