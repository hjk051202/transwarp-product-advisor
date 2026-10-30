"""Project configuration and paths."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MANUAL_DIR = DATA_DIR / "manuals"
DB_PATH = DATA_DIR / "fieldops.db"
CHROMA_DIR = ROOT / ".chroma"
MCP_SERVER = ROOT / "mcp_server" / "cmms_server.py"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

APP_NAME = "设备售后运维助手"
APP_SUBTITLE = "FieldOps Copilot · 设备故障诊断与工单闭环"
