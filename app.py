"""星环产品选型助手 · Streamlit UI."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
import streamlit as st

API_URL = os.getenv("FIELDOPS_API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("FIELDOPS_API_KEY", "")


def new_session_id() -> str:
    return f"SESS-{datetime.now():%Y%m%d%H%M%S}-{uuid4().hex[:4]}"


st.set_page_config(
    page_title="星环产品选型助手",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --brand:#0f766e; --soft:#ccfbf1; }
    .block-container { padding-top:1.2rem; padding-bottom:2rem; max-width:1180px; }
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu { display:none !important; }
    .hero {
        display:flex; justify-content:space-between; gap:1rem; align-items:center;
        padding:1.2rem 1.4rem; border:1px solid var(--line); border-radius:18px;
        background:linear-gradient(135deg,#ffffff 0%,#f0fdfa 100%);
        box-shadow:0 8px 24px rgba(15,23,42,.05); margin-bottom:1.1rem;
    }
    .hero-left { display:flex; gap:.9rem; align-items:center; }
    .hero-icon {
        width:52px; height:52px; border-radius:14px; display:flex;
        align-items:center; justify-content:center; font-size:26px; background:var(--soft);
    }
    .hero-title { font-size:1.65rem; font-weight:800; color:var(--ink); line-height:1.2; }
    .hero-sub { color:var(--muted); font-size:.92rem; margin-top:.2rem; }
    .side-brand {
        display:flex; gap:.7rem; align-items:center; padding:.2rem 0 .9rem 0;
        border-bottom:1px solid var(--line); margin-bottom:.9rem;
    }
    .side-icon {
        width:38px; height:38px; border-radius:11px; display:flex;
        align-items:center; justify-content:center; font-size:19px; background:var(--soft);
    }
    .side-title { font-weight:800; color:var(--ink); font-size:1rem; }
    .side-sub { color:var(--muted); font-size:.72rem; }
    .panel {
        border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem;
        background:#fff; box-shadow:0 4px 14px rgba(15,23,42,.03);
    }
    .panel-title { font-weight:800; color:var(--ink); margin-bottom:.4rem; }
    .muted { color:var(--muted); font-size:.88rem; }
    .badge-ok {
        display:inline-block; padding:.18rem .5rem; border-radius:999px;
        font-size:.72rem; font-weight:700; color:#047857; background:#d1fae5;
    }
    div[data-testid="stMetric"] {
        border:1px solid var(--line); border-radius:12px; padding:.6rem .8rem; background:#fff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "session_id" not in st.session_state:
    st.session_state.session_id = new_session_id()
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "我是**星环产品选型助手**。告诉我行业、数据量、业务负载和国产化要求，"
                "我可以帮你对比 ArgoDB、TDH、TDC、Sophon、StellarDB、KunDB。\n\n"
                "试试：`我们是城商行，TB 级数据，主要做报表和风控分析，ArgoDB 和 TDH 怎么选？`"
            ),
            "citations": [],
            "tools": [],
            "mode": "",
        }
    ]
if "api_url" not in st.session_state:
    st.session_state.api_url = API_URL
if "api_key" not in st.session_state:
    st.session_state.api_key = API_KEY


@st.cache_data(ttl=5, show_spinner=False)
def fetch_health(url: str) -> dict[str, Any] | None:
    try:
        response = httpx.get(f"{url.rstrip('/')}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def post_chat(
    url: str, message: str, session_id: str, company: str, industry: str, key: str
) -> dict[str, Any]:
    response = httpx.post(
        f"{url.rstrip('/')}/chat",
        json={
            "message": message,
            "session_id": session_id,
            "company": company,
            "industry": industry,
        },
        headers={"X-API-Key": key} if key else {},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def fetch_history(url: str, key: str, limit: int = 20) -> list[dict[str, Any]]:
    response = httpx.get(
        f"{url.rstrip('/')}/conversations",
        params={"limit": limit},
        headers={"X-API-Key": key} if key else {},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-left">
            <div class="hero-icon">🧭</div>
            <div>
              <div class="hero-title">星环产品选型助手</div>
              <div class="hero-sub">Transwarp Product Advisor · 产品选型与历史会话</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
          <div class="side-icon">🧭</div>
          <div>
            <div class="side-title">星环产品选型助手</div>
            <div class="side-sub">Transwarp Product Advisor</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "导航", ["选型咨询", "历史会话", "技术栈"], label_visibility="collapsed"
    )
    st.divider()
    api_url_input = st.text_input("后端地址", value=st.session_state.api_url)
    if api_url_input != st.session_state.api_url:
        st.session_state.api_url = api_url_input
    st.session_state.api_key = st.text_input(
        "API Key（可选）", value=st.session_state.api_key, type="password"
    )
    company = st.text_input("客户公司", value="某城商行")
    industry = st.selectbox(
        "行业", ["金融", "政务", "能源", "制造", "交通", "运营商", "其他"], index=0
    )

    st.caption(f"当前会话：`{st.session_state.session_id}`")
    if st.button("新建会话", use_container_width=True):
        st.session_state.session_id = new_session_id()
        st.session_state.messages = st.session_state.messages[:1]
        st.rerun()

    health = fetch_health(st.session_state.api_url)
    if health:
        st.markdown(
            f'<span class="badge-ok">● 后端已连接</span> '
            f'<span class="muted">模式：{health.get("mode", "")}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.error("后端未连接")
        st.caption("先运行：uvicorn fieldops.main:app --port 8000")

    if st.button("刷新连接", use_container_width=True):
        fetch_health.clear()
        st.rerun()

render_header()


def render_chat() -> None:
    st.caption(f"客户：{company} · 行业：{industry} · 会话：{st.session_state.session_id}")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("mode"):
                st.caption(f"mode: {message['mode']}")
            citations = message.get("citations") or []
            if citations:
                with st.expander(f"引用来源（{len(citations)}）"):
                    for item in citations:
                        page_no = f"p.{item.get('page')}" if item.get("page") else ""
                        st.markdown(
                            f"**{item.get('title', '')}** "
                            f"{item.get('section', '')} {page_no}  \n"
                            f"`{item.get('doc_id', '')}` · {item.get('product', '')}"
                        )
                        st.caption(item.get("snippet", "")[:300])
            tools = message.get("tools") or []
            if tools:
                with st.expander(f"工具调用轨迹（{len(tools)}）"):
                    for tool in tools:
                        st.markdown(f"**{tool.get('name', '')}**")
                        st.json(tool.get("result", {}))

    prompt = st.chat_input(
        "描述需求，例如：我们是城商行，TB 级数据，做报表和风控，ArgoDB 和 TDH 怎么选？"
    )
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        data = post_chat(
            st.session_state.api_url,
            prompt,
            st.session_state.session_id,
            company,
            industry,
            st.session_state.api_key,
        )
    except Exception as exc:
        st.error(f"后端调用失败：{exc}")
        return

    assistant_message = {
        "role": "assistant",
        "content": data.get("answer", ""),
        "citations": data.get("citations", []),
        "tools": data.get("tool_trace", []),
        "mode": data.get("mode", ""),
    }
    st.session_state.messages.append(assistant_message)

    with st.chat_message("assistant"):
        st.markdown(assistant_message["content"])
        st.caption(f"mode: {assistant_message['mode']}")
        if assistant_message["citations"]:
            with st.expander(f"引用来源（{len(assistant_message['citations'])}）"):
                for item in assistant_message["citations"]:
                    page_no = f"p.{item.get('page')}" if item.get("page") else ""
                    st.markdown(
                        f"**{item.get('title', '')}** "
                        f"{item.get('section', '')} {page_no}  \n"
                        f"`{item.get('doc_id', '')}` · {item.get('product', '')}"
                    )
                    st.caption(item.get("snippet", "")[:300])
        if assistant_message["tools"]:
            with st.expander(f"工具调用轨迹（{len(assistant_message['tools'])}）"):
                for tool in assistant_message["tools"]:
                    st.markdown(f"**{tool.get('name', '')}**")
                    st.json(tool.get("result", {}))

    if data.get("conversation_id"):
        st.caption(f"已保存历史会话：`{data['conversation_id']}`")


def render_history() -> None:
    st.markdown("### 历史会话")
    st.caption("每次问答都会保存到 SQLite；MCP 可用时通过 history-mcp 保存。")
    if st.button("刷新历史", use_container_width=False):
        st.rerun()
    try:
        items = fetch_history(
            st.session_state.api_url, st.session_state.api_key, limit=30
        )
    except Exception as exc:
        st.error(f"读取历史失败：{exc}")
        return

    if not items:
        st.info("还没有历史会话。")
        return

    for item in items:
        title = item.get("user_message", "")[:50] or "未命名会话"
        with st.expander(f"{title} · {item.get('created_at', '')}"):
            st.caption(f"session_id: {item.get('session_id', '')}")
            st.markdown(f"**用户**：{item.get('user_message', '')}")
            st.markdown(f"**助手**：{item.get('assistant_message', '')}")
            citations = item.get("citations") or []
            if citations:
                st.caption(f"引用 {len(citations)} 条")
                for citation in citations:
                    st.markdown(
                        f"- {citation.get('title', '')} "
                        f"{citation.get('section', '')}（{citation.get('doc_id', '')}）"
                    )


def render_stack() -> None:
    st.markdown("### 4 + 1 项核心能力")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("知识文档", "12 份")
    c2.metric("MCP Server", "1 个")
    c3.metric("原生工具", "5 个")
    c4.metric("历史会话", "SQLite")

    st.markdown("### 技术栈解决的实际问题")
    st.dataframe(
        [
            {
                "技术": "LangChain",
                "解决的实际问题": "选型咨询是多步流程，if/else 会越来越乱",
                "本项目的实现": "create_agent 统一调度 RAG 和产品工具",
            },
            {
                "技术": "RAG",
                "解决的实际问题": "产品资料、案例、兼容性散落在官网/白皮书",
                "本项目的实现": "产品文档切分 + 引用 + Chroma 检索",
            },
            {
                "技术": "Tool Calling",
                "解决的实际问题": "产品对比、案例、兼容性不能靠模型记忆",
                "本项目的实现": "list / compare / cases / compatibility",
            },
            {
                "技术": "MCP",
                "解决的实际问题": "历史会话要跨进程持久化、可复用",
                "本项目的实现": "history-mcp 暴露 save/get/list conversation",
            },
            {
                "技术": "历史会话",
                "解决的实际问题": "用户关闭页面后还能回看之前问过什么",
                "本项目的实现": "conversations 表 + 历史会话页面",
            },
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### 运行架构")
    st.code(
        "Streamlit UI\n"
        "  -> FastAPI /chat\n"
        "    -> LangChain create_agent\n"
        "      -> Chroma RAG (search_knowledge)\n"
        "      -> Native tools (list/compare/cases/compatibility)\n"
        "    -> history-mcp (save_conversation)\n"
        "      -> SQLite conversations",
        language="text",
    )
    st.info(
        "没有模型 API Key 时使用确定性离线模型，仍走 LangChain create_agent；"
        "配置 DEEPSEEK_API_KEY 后切换真实模型。"
    )


if page == "选型咨询":
    render_chat()
elif page == "历史会话":
    render_history()
else:
    render_stack()
