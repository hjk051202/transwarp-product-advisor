"""星环产品选型助手 · Streamlit UI."""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

API_URL = os.getenv("FIELDOPS_API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("FIELDOPS_API_KEY", "")

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
    .hero-tags { display:flex; flex-wrap:wrap; gap:.4rem; justify-content:flex-end; }
    .tag {
        font-size:.72rem; font-weight:700; color:var(--brand); background:var(--soft);
        border-radius:999px; padding:.28rem .6rem; white-space:nowrap;
    }
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
if "lead" not in st.session_state:
    st.session_state.lead = None
if "crm_lead" not in st.session_state:
    st.session_state.crm_lead = None
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
    url: str, message: str, company: str, industry: str, contact: str, key: str
) -> dict[str, Any]:
    response = httpx.post(
        f"{url.rstrip('/')}/chat",
        json={
            "message": message,
            "company": company,
            "industry": industry,
            "contact": contact,
        },
        headers={"X-API-Key": key} if key else {},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def post_approve(url: str, lead_id: str, key: str) -> dict[str, Any]:
    response = httpx.post(
        f"{url.rstrip('/')}/leads/{lead_id}/approve",
        headers={"X-API-Key": key} if key else {},
        timeout=60,
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
              <div class="hero-sub">Transwarp Product Advisor · 产品选型与售前线索</div>
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
        "导航", ["选型咨询", "线索草稿", "技术栈"], label_visibility="collapsed"
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
    contact = st.text_input("联系方式", value="demo@example.com")

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
        st.session_state.lead = None
        st.session_state.crm_lead = None
        st.rerun()

render_header()


def render_chat() -> None:
    st.caption(f"客户：{company} · 行业：{industry} · 后端：{st.session_state.api_url}")
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
            company,
            industry,
            contact,
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
    st.session_state.lead = data.get("lead")
    st.session_state.crm_lead = None

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
                        f"`{item.get('doc_id', '')}` · {item.get('product', '')}"
                    )
                    st.caption(item.get("snippet", "")[:300])
        if assistant_message["tools"]:
            with st.expander(f"工具调用轨迹（{len(assistant_message['tools'])}）"):
                for tool in assistant_message["tools"]:
                    st.markdown(f"**{tool.get('name', '')}**")
                    st.json(tool.get("result", {}))

    if st.session_state.lead:
        st.info("线索草稿已生成，去左侧「线索草稿」确认。")


def render_lead() -> None:
    lead = st.session_state.lead
    if not lead:
        st.markdown(
            '<div class="panel"><div class="panel-title">还没有线索草稿</div>'
            '<div class="muted">先在「选型咨询」里描述需求，例如 ArgoDB 和 TDH 怎么选，'
            "助手会在识别到选型/试用/报价意向时生成草稿。</div></div>",
            unsafe_allow_html=True,
        )
        return

    if st.session_state.crm_lead:
        crm = st.session_state.crm_lead
        st.success(f"线索已写入 CRM：{crm.get('crm_lead_id')}")
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-title">CRM 线索已创建</div>
              <div class="muted">
                CRM 线索号：<b>{crm.get('crm_lead_id')}</b><br/>
                本地草稿号：{crm.get('lead_id')}<br/>
                状态：{crm.get('status')}<br/>
                写入路径：crm-mcp.create_lead
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div class="panel"><div class="panel-title">售前线索草稿 · 待人工确认</div>'
        '<div class="muted">写操作不会自动执行。请核对客户、行业、需求和推荐产品后批准。</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("行业", lead.get("industry", "-"))
    c2.metric("推荐产品", " / ".join(lead.get("products") or []) or "待确认")
    c3.metric("状态", lead.get("status", "draft"))

    st.markdown("**客户与需求**")
    st.markdown(
        f"""
        - 公司：{lead.get('company')}
        - 行业：{lead.get('industry')}
        - 联系方式：{lead.get('contact')}
        - 需求：{lead.get('need')}
        - 草稿号：`{lead.get('lead_id')}`
        """
    )

    st.markdown("**推荐产品**")
    st.write(lead.get("products") or "待确认")

    if st.button("批准并写入 CRM", type="primary"):
        try:
            with st.spinner("正在通过 crm-mcp 创建线索..."):
                result = post_approve(
                    st.session_state.api_url,
                    lead["lead_id"],
                    st.session_state.api_key,
                )
            st.session_state.crm_lead = result
            st.rerun()
        except Exception as exc:
            st.error(f"写入失败：{exc}")


def render_stack() -> None:
    st.markdown("### 4 + 1 项核心能力")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("知识文档", "9 份")
    c2.metric("MCP Server", "1 个")
    c3.metric("原生工具", "6 个")
    c4.metric("写操作审批", "1 个入口")

    st.markdown("### 技术栈解决的实际问题")
    st.dataframe(
        [
            {
                "技术": "LangChain",
                "解决的实际问题": "选型咨询是多步流程，if/else 会越来越乱",
                "本项目的实现": "create_agent 统一调度 RAG、产品工具、MCP 工具",
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
                "解决的实际问题": "CRM 是外部系统，留资要认证、审计、复用",
                "本项目的实现": "crm-mcp 暴露 create_lead / get_lead",
            },
            {
                "技术": "HITL",
                "解决的实际问题": "线索写错会影响销售跟进",
                "本项目的实现": "Agent 只出 draft，售前确认后才写 CRM",
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
        "      -> Native tools (list/compare/cases/compatibility/draft)\n"
        "      -> crm-mcp (create_lead / get_lead)\n"
        "        -> SQLite CRM mock",
        language="text",
    )
    st.info(
        "没有模型 API Key 时使用确定性离线模型，仍走 LangChain create_agent；"
        "配置 DEEPSEEK_API_KEY 后切换真实模型。"
    )


if page == "选型咨询":
    render_chat()
elif page == "线索草稿":
    render_lead()
else:
    render_stack()

st.divider()
st.caption("星环产品选型助手 · LangChain + RAG + Tool Calling + MCP")
