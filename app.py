"""星环产品选型助手 · Streamlit UI."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from uuid import uuid4

import streamlit as st

from fieldops.service import chat as service_chat
from fieldops.service import list_history


def new_session_id() -> str:
    return f"SESS-{datetime.now():%Y%m%d%H%M%S}-{uuid4().hex[:4]}"


def run(coro):
    return asyncio.run(coro)


st.set_page_config(
    page_title="星环产品选型助手",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #f4f7fb;
        --panel: #ffffff;
        --panel-2: #f8fafc;
        --line: #d9e3f0;
        --line-soft: #e6edf6;
        --text: #0f172a;
        --muted: #64748b;
        --accent: #0f766e;
        --accent-2: #0f766e;
        --ok: #059669;
    }
    html, body, [class*="css"] {
        font-family: "Inter", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    .stApp {
        background:
            radial-gradient(900px 420px at 18% -8%, rgba(37, 99, 235, .07), transparent 60%),
            radial-gradient(760px 380px at 100% 0%, rgba(13, 148, 136, .06), transparent 55%),
            var(--bg);
        color: var(--text);
    }
    .block-container {
        max-width: 1220px;
        padding-top: 1.1rem;
        padding-bottom: 2.5rem;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stDecoration"],
    #MainMenu { display: none !important; }
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: block !important;
        visibility: visible !important;
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line-soft);
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--muted);
    }
    section[data-testid="stSidebar"] input {
        color: var(--text);
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 0 0.8rem 0;
        border-bottom: 1px solid var(--line-soft);
        margin-bottom: 1.2rem;
    }
    .crumb {
        color: var(--muted);
        font-size: 0.78rem;
        letter-spacing: .02em;
    }
    .crumb b { color: var(--text); font-weight: 600; }
    .crumb .sep { color: #40516a; margin: 0 .45rem; }
    .top-meta {
        display: flex;
        align-items: center;
        gap: .45rem;
        color: var(--muted);
        font-size: .72rem;
    }
    .live-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: var(--ok); box-shadow: 0 0 10px rgba(52, 211, 153, .7);
    }
    .version {
        border: 1px solid var(--line);
        color: #9fb1c9;
        border-radius: 999px;
        padding: .12rem .45rem;
        font-size: .66rem;
    }

    .workspace-head {
        margin: .2rem 0 1.15rem 0;
        max-width: 860px;
    }
    .eyebrow {
        color: var(--accent-2);
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: .16em;
        text-transform: uppercase;
        margin-bottom: .45rem;
    }
    .workspace-head h1 {
        color: var(--text);
        font-size: 1.9rem;
        line-height: 1.2;
        letter-spacing: -.02em;
        margin: 0 0 .4rem 0;
        font-weight: 750;
    }
    .workspace-head p {
        color: var(--muted);
        font-size: .9rem;
        line-height: 1.65;
        margin: 0;
    }

    .empty-state {
        border: 1px solid var(--line-soft);
        background: linear-gradient(135deg, rgba(18, 28, 45, .88), rgba(12, 19, 31, .9));
        border-radius: 16px;
        padding: 1.05rem 1.15rem;
        margin: .3rem 0 .8rem 0;
    }
    .empty-title {
        color: var(--text);
        font-size: 1rem;
        font-weight: 650;
        margin-bottom: .3rem;
    }
    .empty-copy {
        color: var(--muted);
        font-size: .82rem;
        line-height: 1.6;
    }
    .sample-label {
        color: #718198;
        font-size: .68rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin: .8rem 0 .45rem 0;
    }

    .side-brand {
        display: flex; align-items: center; gap: .7rem;
        padding: .1rem 0 .9rem 0;
        border-bottom: 1px solid var(--line-soft);
        margin-bottom: .9rem;
    }
    .brand-mark {
        width: 38px; height: 38px; border-radius: 11px;
        display: flex; align-items: center; justify-content: center;
        color: #071018; font-weight: 800; font-size: .78rem;
        background: linear-gradient(135deg, #8bc5ff, #4dd4c6);
        letter-spacing: -.04em;
    }
    .side-title { color: var(--text); font-size: .9rem; font-weight: 700; line-height: 1.25; }
    .side-sub { color: #63748c; font-size: .66rem; margin-top: .15rem; letter-spacing: .04em; }
    .side-section {
        color: #718198; font-size: .64rem; letter-spacing: .12em;
        text-transform: uppercase; margin: .4rem 0 .35rem 0;
    }
    .side-status {
        margin-top: 1.2rem; padding: .75rem .8rem;
        border: 1px solid var(--line-soft); border-radius: 10px;
        background: rgba(13, 20, 32, .7); color: #a9b8cb; font-size: .72rem;
    }
    .side-status .dot {
        display: inline-block; width: 6px; height: 6px; border-radius: 50%;
        background: var(--ok); margin-right: .4rem;
    }
    .side-status-sub { color: #5f7087; font-size: .65rem; margin-top: .3rem; }

    [data-testid="stChatMessage"] {
        background: rgba(15, 22, 36, .72);
        border: 1px solid var(--line-soft);
        border-radius: 14px;
        padding: .75rem .95rem;
        margin-bottom: .55rem;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: var(--text);
        font-size: .91rem;
        line-height: 1.72;
    }
    [data-testid="stChatMessage"] h3 {
        color: #dce8f8;
        font-size: 1rem;
        margin: .65rem 0 .35rem 0;
    }
    [data-testid="stChatMessage"] code {
        color: #9ed0ff;
        background: rgba(110, 168, 254, .1);
    }
    .msg-label {
        color: #6d7e96; font-size: .64rem; letter-spacing: .08em;
        text-transform: uppercase; margin-bottom: .2rem;
    }
    .citation-item {
        border-left: 2px solid #315b8f;
        padding-left: .6rem;
        margin: .55rem 0;
    }
    .citation-title { color: #cfe2fa; font-size: .8rem; font-weight: 650; }
    .citation-meta { color: #6f8198; font-size: .68rem; margin-top: .12rem; }
    .citation-snippet { color: #8fa2b9; font-size: .72rem; line-height: 1.55; margin-top: .25rem; }
    .page-title {
        color: var(--text); font-size: 1.5rem; font-weight: 750;
        letter-spacing: -.02em; margin: .2rem 0 .25rem 0;
    }
    .page-sub { color: var(--muted); font-size: .82rem; margin-bottom: 1rem; }
    .history-question { color: #d6e4f5; font-size: .86rem; font-weight: 600; }
    .history-time { color: #65768e; font-size: .68rem; text-align: right; }
    .history-session { color: #5f7087; font-size: .66rem; margin-top: .25rem; }
    div[data-testid="stMetric"] {
        background: rgba(15, 22, 36, .72);
        border: 1px solid var(--line-soft);
        border-radius: 12px;
        padding: .65rem .8rem;
    }
    div[data-testid="stMetric"] label { color: var(--muted); }
    div[data-testid="stMetricValue"] { color: var(--text); font-size: 1.35rem; }
    .stCaption, [data-testid="stCaptionContainer"] { color: #6f8198 !important; }
    div[data-testid="stExpander"] {
        border: 1px solid var(--line-soft);
        border-radius: 10px;
        background: rgba(10, 16, 26, .55);
    }

    /* Light workspace overrides */
    .crumb .sep { color: #94a3b8; }
    .version { color: #64748b; }
    .empty-state {
        background: linear-gradient(135deg, #ffffff, #f8fafc) !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, .04);
    }
    .sample-label { color: #64748b; }
    .brand-mark { color: #ffffff; background: linear-gradient(135deg, #0f766e, #2563eb); }
    .side-sub { color: #64748b; }
    .side-section { color: #64748b; }
    .side-status {
        background: #f8fafc !important;
        color: #475569 !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, .03);
    }
    .side-status-sub { color: #94a3b8; }
    [data-testid="stChatMessage"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, .04);
    }
    [data-testid="stChatMessage"] h3 { color: #0f172a !important; }
    [data-testid="stChatMessage"] code {
        color: #0f766e !important;
        background: rgba(15, 118, 110, .08) !important;
    }
    .msg-label { color: #64748b; }
    .citation-item { border-left-color: #0f766e; }
    .citation-title { color: #0f172a; }
    .citation-meta { color: #64748b; }
    .citation-snippet { color: #475569; }
    .history-question { color: #0f172a; }
    .history-time { color: #64748b; }
    .history-session { color: #94a3b8; }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, .03);
    }
    div[data-testid="stMetricValue"] { color: #0f172a !important; }
    .stCaption, [data-testid="stCaptionContainer"] { color: #64748b !important; }
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "session_id" not in st.session_state:
    st.session_state.session_id = new_session_id()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


def queue_prompt(text: str) -> None:
    st.session_state.pending_prompt = text


def mode_label(mode: str) -> str:
    return {
        "offline-mock": "本地演示",
        "offline-fallback": "本地兜底",
        "deepseek": "DeepSeek",
        "openai": "OpenAI",
    }.get(mode, mode or "本地")


def render_topbar(page: str) -> None:
    crumbs = {
        "工作台": "选型咨询",
        "历史会话": "历史会话",
        "技术栈": "技术栈",
    }
    st.markdown(
        f"""
        <div class="topbar">
          <div class="crumb">星环产品选型助手 <span class="sep">/</span>
            <b>{crumbs.get(page, page)}</b></div>
          <div class="top-meta">
            <span class="live-dot"></span> 本地运行
            <span class="version">v1.0</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_answer(text: str) -> None:
    main, _, small = text.partition("<!-- SMALL -->")
    st.markdown(main.strip())
    if small.strip():
        lines = []
        for line in small.splitlines():
            stripped = line.strip()
            if stripped.startswith("### "):
                lines.append(f"**{stripped[4:]}**")
            elif stripped:
                lines.append(stripped)
        st.caption("\n".join(lines))


def render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    with st.expander(f"引用来源 · {len(citations)}", expanded=False):
        for item in citations:
            page = f" · p.{item.get('page')}" if item.get("page") else ""
            st.markdown(
                f"""
                <div class="citation-item">
                  <div class="citation-title">{item.get("title", "")}</div>
                  <div class="citation-meta">{item.get("doc_id", "")}
                    · {item.get("section", "")}{page} · {item.get("product", "")}</div>
                  <div class="citation-snippet">{item.get("snippet", "")[:280]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_tools(tools: list[dict]) -> None:
    if not tools:
        return
    with st.expander(f"执行轨迹 · {len(tools)}", expanded=False):
        for tool in tools:
            st.markdown(f"**`{tool.get('name', '')}`**")
            result = json.dumps(tool.get("result", {}), ensure_ascii=False, indent=2)
            st.code(result[:1400], language="json")


def render_message(message: dict) -> None:
    role = message.get("role", "assistant")
    with st.chat_message(role, avatar="🧭" if role == "assistant" else "👤"):
        if role == "assistant":
            st.markdown(
                f'<div class="msg-label">ADVISOR · {mode_label(message.get("mode", ""))}</div>',
                unsafe_allow_html=True,
            )
            render_answer(message.get("content", ""))
            render_citations(message.get("citations") or [])
            render_tools(message.get("tools") or [])
        else:
            st.markdown(message.get("content", ""))


def render_welcome() -> None:
    st.markdown(
        """
        <div class="empty-state">
          <div class="empty-title">从一个客户需求开始</div>
          <div class="empty-copy">
            描述客户的行业、数据量、业务负载和部署要求。助手会检索产品资料、
            对比候选产品，并给出可追溯的引用来源。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sample-label">快速开始</div>', unsafe_allow_html=True)
    samples = [
        ("对比 ArgoDB / TDH", "ArgoDB 和 TDH 怎么选？"),
        ("银行报表场景", "我是一个银行的，搞报表，数据量GB，无国产要求"),
        ("国产化兼容性", "我们要求麒麟 + 鲲鹏国产化，ArgoDB 支持吗？"),
    ]
    columns = st.columns(3)
    for column, (label, prompt) in zip(columns, samples):
        with column:
            st.button(
                label,
                key=f"sample-{label}",
                on_click=queue_prompt,
                args=(prompt,),
                use_container_width=True,
            )


def render_chat() -> None:
    for message in st.session_state.messages:
        render_message(message)

    if not st.session_state.messages:
        render_welcome()

    pending = st.session_state.pop("pending_prompt", None)
    prompt = st.chat_input(
        "描述客户需求，例如：城商行，TB 级数据，做报表和风控，ArgoDB 和 TDH 怎么选？"
    )
    prompt = prompt or pending
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    history_payload = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.messages[:-1][-8:]
        if item.get("role") in {"user", "assistant"}
    ]

    try:
        with st.spinner("正在检索产品资料并生成建议…"):
            data = run(
                service_chat(
                    prompt,
                    session_id=st.session_state.session_id,
                    company=company,
                    industry=industry,
                    history=history_payload,
                )
            )
    except Exception as exc:
        st.error(f"调用失败：{exc}")
        return

    payload = data.model_dump()
    assistant_message = {
        "role": "assistant",
        "content": payload["answer"],
        "citations": payload["citations"],
        "tools": payload["tool_trace"],
        "mode": payload["mode"],
    }
    st.session_state.messages.append(assistant_message)
    render_message(assistant_message)

    if payload.get("conversation_id"):
        st.caption(f"已保存 · {payload['conversation_id']}")


def render_history() -> None:
    st.markdown('<div class="page-title">历史会话</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">每次问答自动保存到 SQLite；可回看回答、引用和工具轨迹。</div>',
        unsafe_allow_html=True,
    )
    query = st.text_input(
        "搜索历史",
        placeholder="按客户问题搜索…",
        label_visibility="collapsed",
    )
    try:
        items = run(list_history(limit=40))
    except Exception as exc:
        st.error(f"读取历史失败：{exc}")
        return

    if query:
        needle = query.lower()
        items = [
            item
            for item in items
            if needle
            in (item.get("user_message", "") + item.get("assistant_message", "")).lower()
        ]

    st.caption(f"共 {len(items)} 条")
    if not items:
        st.info("还没有历史会话。")
        return

    for item in items:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(
                    f'<div class="history-question">{item.get("user_message", "")[:120]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="history-session">SESSION · {item.get("session_id", "")}</div>',
                    unsafe_allow_html=True,
                )
            with right:
                created = str(item.get("created_at", ""))[:16].replace("T", " ")
                st.markdown(
                    f'<div class="history-time">{created}</div>',
                    unsafe_allow_html=True,
                )
            with st.expander("查看回答与引用", expanded=False):
                render_answer(item.get("assistant_message", ""))
                render_citations(item.get("citations") or [])
                render_tools(item.get("tool_trace") or [])


def render_stack() -> None:
    st.markdown('<div class="page-title">技术栈</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">一个本地优先的产品选型 Agent：RAG、Tool Calling、MCP 和可回看的会话。</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("知识文档", "12", "10 Markdown + 2 PDF")
    c2.metric("原生工具", "5", "检索 / 对比 / 案例")
    c3.metric("MCP 工具", "3", "历史会话")
    c4.metric("测试", "15", "pytest")

    st.markdown("### 核心链路")
    st.code(
        "Streamlit\n"
        "  → service.chat\n"
        "    → LangChain create_agent\n"
        "      → 5 个原生工具 → RAG / products.json / cases.json\n"
        "    → history adapter → history-mcp → SQLite\n"
        "  → 引用 + 工具轨迹 + 历史会话",
        language="text",
    )

    st.markdown("### 技术选择")
    st.dataframe(
        [
            {
                "技术": "LangChain",
                "作用": "Agent 编排与 Tool Calling",
                "项目实现": "create_agent + 5 个工具",
            },
            {
                "技术": "Chroma + BM25",
                "作用": "产品资料检索与引用",
                "项目实现": "混合召回 + RRF",
            },
            {
                "技术": "MCP / FastMCP",
                "作用": "历史会话服务边界",
                "项目实现": "save / get / list conversation",
            },
            {
                "技术": "SQLite",
                "作用": "本地会话持久化",
                "项目实现": "conversations + audit_log",
            },
            {
                "技术": "Streamlit",
                "作用": "单进程交互界面",
                "项目实现": "聊天、引用、历史",
            },
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### 当前边界")
    st.markdown(
        "- 12 份文档、19 个 chunk，小型合成评测，不代表生产泛化。\n"
        "- 默认离线模型 + HashingEmbeddings；外部 LLM/Embedding 可选，但未在本环境验证。\n"
        "- 没有多用户登录、权限和分布式存储；当前是本地单用户 Demo。"
    )


def render_sidebar() -> tuple[str, str, str]:
    with st.sidebar:
        st.markdown(
            """
            <div class="side-brand">
              <div class="brand-mark">TW</div>
              <div>
                <div class="side-title">星环产品选型</div>
                <div class="side-sub">PRODUCT ADVISOR</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("＋ 新建会话", type="primary", use_container_width=True):
            st.session_state.session_id = new_session_id()
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()

        page = st.radio(
            "导航",
            ["工作台", "历史会话", "技术栈"],
            label_visibility="collapsed",
        )

        st.markdown('<div class="side-section">会话参数</div>', unsafe_allow_html=True)
        company = st.text_input("客户公司", value="某城商行")
        industry = st.selectbox(
            "行业",
            ["金融", "政务", "能源", "制造", "交通", "运营商", "其他"],
            index=0,
        )

        st.markdown(
            f"""
            <div class="side-status">
              <span class="dot"></span> 本地运行
              <div class="side-status-sub">SESSION · {st.session_state.session_id}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return page, company, industry


page, company, industry = render_sidebar()
render_topbar(page)

if page == "工作台":
    st.markdown(
        """
        <div class="workspace-head">
          <div class="eyebrow">TRANS WARP · PRODUCT ADVISOR</div>
          <h1>星环产品选型助手</h1>
          <p>描述客户需求，助手会检索产品资料、对比候选产品，并给出可追溯的依据。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_chat()
elif page == "历史会话":
    render_history()
else:
    render_stack()
