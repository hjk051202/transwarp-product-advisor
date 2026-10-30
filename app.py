"""设备售后运维助手 · FastAPI-backed Streamlit UI.

Run:
    uvicorn fieldops.main:app --port 8000
    streamlit run app.py

The page talks to the backend over HTTP; it never imports the agent directly.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

API_URL = os.getenv("FIELDOPS_API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("FIELDOPS_API_KEY", "")

st.set_page_config(
    page_title="设备售后运维助手",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --brand: #0f766e;
        --brand-soft: #ccfbf1;
    }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1180px; }
    .hero {
        display: flex; justify-content: space-between; gap: 1rem; align-items: center;
        padding: 1.2rem 1.4rem; border: 1px solid var(--line); border-radius: 18px;
        background: linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%);
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); margin-bottom: 1.1rem;
    }
    .hero-left { display: flex; gap: 0.9rem; align-items: center; }
    .hero-icon {
        width: 52px; height: 52px; border-radius: 14px; display: flex;
        align-items: center; justify-content: center; font-size: 26px;
        background: var(--brand-soft);
    }
    .hero-title { font-size: 1.65rem; font-weight: 800; color: var(--ink); line-height: 1.2; }
    .hero-sub { color: var(--muted); font-size: 0.92rem; margin-top: 0.2rem; }
    .hero-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: flex-end; }
    .tag {
        font-size: 0.72rem; font-weight: 700; color: var(--brand);
        background: var(--brand-soft); border-radius: 999px;
        padding: 0.28rem 0.6rem; white-space: nowrap;
    }
    .side-brand {
        display: flex; gap: 0.7rem; align-items: center;
        padding: 0.2rem 0 0.9rem 0; border-bottom: 1px solid var(--line);
        margin-bottom: 0.9rem;
    }
    .side-icon {
        width: 38px; height: 38px; border-radius: 11px; display: flex;
        align-items: center; justify-content: center; font-size: 19px;
        background: var(--brand-soft);
    }
    .side-title { font-weight: 800; color: var(--ink); font-size: 1rem; }
    .side-sub { color: var(--muted); font-size: 0.72rem; }
    .panel {
        border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.1rem;
        background: #ffffff; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
    }
    .panel-title { font-weight: 800; color: var(--ink); margin-bottom: 0.4rem; }
    .muted { color: var(--muted); font-size: 0.88rem; }
    .badge-ok {
        display: inline-block; padding: 0.18rem 0.5rem; border-radius: 999px;
        font-size: 0.72rem; font-weight: 700; color: #047857; background: #d1fae5;
    }
    div[data-testid="stMetric"] {
        border: 1px solid var(--line); border-radius: 12px;
        padding: 0.6rem 0.8rem; background: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "我是**设备售后运维助手**。我可以查设备工况、保修、备件和维修手册，"
                "并在诊断后生成一份待确认的工单草稿。\n\n"
                "试试输入：`X100 报 E-204，出水温度高，客户已停机。`"
            ),
            "citations": [],
            "tools": [],
            "mode": "",
        }
    ]
if "draft" not in st.session_state:
    st.session_state.draft = None
if "work_order" not in st.session_state:
    st.session_state.work_order = None
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


def post_chat(url: str, message: str, serial: str, key: str = "") -> dict[str, Any]:
    headers = {"X-API-Key": key} if key else {}
    response = httpx.post(
        f"{url.rstrip('/')}/chat",
        json={"message": message, "serial": serial},
        headers=headers,
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def post_approve(url: str, draft_id: str, key: str = "") -> dict[str, Any]:
    headers = {"X-API-Key": key} if key else {}
    response = httpx.post(
        f"{url.rstrip('/')}/work-orders/{draft_id}/approve",
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-left">
            <div class="hero-icon">🛠️</div>
            <div>
              <div class="hero-title">设备售后运维助手</div>
              <div class="hero-sub">FieldOps Copilot · 设备故障诊断与工单闭环</div>
            </div>
          </div>
          <div class="hero-tags">
            <span class="tag">LangChain</span>
            <span class="tag">RAG</span>
            <span class="tag">Tool Calling</span>
            <span class="tag">MCP</span>
            <span class="tag">HITL</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
          <div class="side-icon">🛠️</div>
          <div>
            <div class="side-title">设备售后运维助手</div>
            <div class="side-sub">FieldOps Copilot</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "导航",
        ["对话诊断", "工单草稿", "技术栈"],
        label_visibility="collapsed",
    )

    st.divider()
    api_url_input = st.text_input("后端地址", value=st.session_state.api_url)
    if api_url_input != st.session_state.api_url:
        st.session_state.api_url = api_url_input
    st.session_state.api_key = st.text_input(
        "API Key（可选）",
        value=st.session_state.api_key,
        type="password",
    )
    serial = st.text_input("设备序列号", value="8F2-1042")
    model = st.selectbox(
        "设备型号",
        ["X100 空压机", "X200 冷水机组", "LabTemp 恒温箱"],
        index=0,
    )

    health = fetch_health(st.session_state.api_url)
    if health:
        st.markdown(
            f'<span class="badge-ok">● 后端已连接</span> '
            f'<span class="muted">模式：{health.get("mode", "")}</span>',
            unsafe_allow_html=True,
        )
        mcp_tools = health.get("mcp_tools", [])
        st.caption("MCP：" + (", ".join(mcp_tools) if mcp_tools else "未连接"))
    else:
        st.error("后端未连接")
        st.caption("先运行：uvicorn fieldops.main:app --port 8000")

    if st.button("刷新连接", use_container_width=True):
        fetch_health.clear()
        st.rerun()

    if st.button("清空对话", use_container_width=True):
        st.session_state.messages = st.session_state.messages[:1]
        st.session_state.draft = None
        st.session_state.work_order = None
        st.rerun()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

render_header()


def render_chat() -> None:
    st.caption(
        f"设备：{model} · SN {serial} · 后端：{st.session_state.api_url}"
    )
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("mode"):
                st.caption(f"mode: {message['mode']}")
            citations = message.get("citations") or []
            if citations:
                with st.expander(f"引用来源（{len(citations)}）"):
                    for item in citations:
                        page = f"p.{item.get('page')}" if item.get("page") else ""
                        st.markdown(
                            f"**{item.get('title', '')}** "
                            f"{item.get('section', '')} {page}  \n"
                            f"`{item.get('doc_id', '')}`"
                        )
                        st.caption(item.get("snippet", "")[:300])
            tools = message.get("tools") or []
            if tools:
                with st.expander(f"工具调用轨迹（{len(tools)}）"):
                    for tool in tools:
                        st.markdown(f"**{tool.get('name', '')}**")
                        st.json(tool.get("result", {}))

    prompt = st.chat_input("描述故障现象，例如：X100 报 E-204，出水温度高，已停机")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        data = post_chat(
            st.session_state.api_url,
            prompt,
            serial,
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
    st.session_state.draft = data.get("draft")
    st.session_state.work_order = None

    with st.chat_message("assistant"):
        st.markdown(assistant_message["content"])
        st.caption(f"mode: {assistant_message['mode']}")
        if assistant_message["citations"]:
            with st.expander(f"引用来源（{len(assistant_message['citations'])}）"):
                for item in assistant_message["citations"]:
                    page = f"p.{item.get('page')}" if item.get("page") else ""
                    st.markdown(
                        f"**{item.get('title', '')}** "
                        f"{item.get('section', '')} {page}  \n"
                        f"`{item.get('doc_id', '')}`"
                    )
                    st.caption(item.get("snippet", "")[:300])
        if assistant_message["tools"]:
            with st.expander(f"工具调用轨迹（{len(assistant_message['tools'])}）"):
                for tool in assistant_message["tools"]:
                    st.markdown(f"**{tool.get('name', '')}**")
                    st.json(tool.get("result", {}))

    if st.session_state.draft:
        st.info("工单草稿已生成，去左侧「工单草稿」确认。")


def render_order() -> None:
    draft = st.session_state.draft
    if not draft:
        st.markdown(
            '<div class="panel"><div class="panel-title">还没有工单草稿</div>'
            '<div class="muted">先在「对话诊断」里描述一个故障，例如 E-204 高温，'
            "助手会自动生成草稿。</div></div>",
            unsafe_allow_html=True,
        )
        return

    if st.session_state.work_order:
        work_order = st.session_state.work_order
        st.success(f"工单已创建：{work_order.get('work_order_id')}")
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-title">工单已写入 CMMS</div>
              <div class="muted">
                工单号：<b>{work_order.get('work_order_id')}</b><br/>
                草稿号：{work_order.get('draft_id')}<br/>
                状态：{work_order.get('status')}<br/>
                写入路径：cmms-mcp.create_work_order
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div class="panel"><div class="panel-title">工单草稿 · 待人工确认</div>'
        '<div class="muted">写操作不会自动执行。请核对故障、备件和安全提示后批准。</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("优先级", draft.get("priority", "P2"))
    c2.metric("预计工时", "1.5 h")
    c3.metric("建议上门", draft.get("scheduled_at") or "待定")

    st.markdown("**设备与故障**")
    st.markdown(
        f"""
        - 设备：{model} · SN `{draft.get('asset_id', serial)}`
        - 草稿号：`{draft.get('draft_id')}`
        - 标题：{draft.get('title')}
        - 描述：{draft.get('description')}
        """
    )

    st.markdown("**备件清单**")
    st.write(draft.get("parts") or "无")

    st.markdown("**安全提示**")
    for item in draft.get("safety") or []:
        st.warning(item)

    if st.button("批准并创建工单", type="primary"):
        try:
            with st.spinner("正在通过 cmms-mcp 创建工单..."):
                result = post_approve(
                    st.session_state.api_url,
                    draft["draft_id"],
                    st.session_state.api_key,
                )
            st.session_state.work_order = result
            st.rerun()
        except Exception as exc:
            st.error(f"创建失败：{exc}")


def render_stack() -> None:
    st.markdown("### 4 + 1 项核心能力")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("知识库文档", "6 份")
    c2.metric("MCP Server", "1 个")
    c3.metric("原生工具", "5 个")
    c4.metric("写操作审批", "1 个入口")

    st.markdown("### 技术栈解决的实际问题")
    st.dataframe(
        [
            {
                "技术": "LangChain",
                "解决的实际问题": "故障处理是多步流程，if/else 会越来越乱",
                "本项目的实现": "create_agent 统一调度 RAG、原生工具、MCP 工具",
            },
            {
                "技术": "RAG",
                "解决的实际问题": "手册长、版本多，模型直接答会编造故障码",
                "本项目的实现": "标题切分 + 元数据过滤 + 页码引用 + Chroma",
            },
            {
                "技术": "Tool Calling",
                "解决的实际问题": "设备实时工况、保修、库存不在文档里",
                "本项目的实现": "get_telemetry / check_warranty / check_parts",
            },
            {
                "技术": "MCP",
                "解决的实际问题": "CMMS 是外部系统，建单要认证、审计、复用",
                "本项目的实现": "cmms-mcp 暴露 create_work_order / get_work_order",
            },
            {
                "技术": "HITL",
                "解决的实际问题": "建单、订备件有真实成本，误操作代价高",
                "本项目的实现": "Agent 只出 draft，工程师批准后才写 CMMS",
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
        "      -> Native tools (telemetry / warranty / parts / draft)\n"
        "      -> cmms-mcp (create_work_order / get_work_order)\n"
        "        -> SQLite CMMS mock",
        language="text",
    )

    st.info(
        "当前为离线可运行模式：没有模型 API Key 时使用确定性 MockToolCallingModel，"
        "仍然走 LangChain create_agent；配置 DEEPSEEK_API_KEY 后自动切换真实模型。"
    )


if page == "对话诊断":
    render_chat()
elif page == "工单草稿":
    render_order()
else:
    render_stack()

st.divider()
st.caption(
    "设备售后运维助手 · FieldOps Copilot · LangChain + RAG + Tool Calling + MCP"
)
