"""设备售后运维助手 · Streamlit 演示界面

运行：
    pip install -r requirements-ui.txt
    streamlit run app.py

说明：
    当前是 Mock 演示模式，不依赖 AgentChat 后端。
    接入真实后端时，把 build_response() / create_work_order() 里的
    Mock 逻辑替换成 AgentChat 的 API 调用即可。
"""

from __future__ import annotations

import time
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# 页面配置
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="设备售后运维助手",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 样式
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --brand: #0f766e;
        --brand-soft: #ccfbf1;
        --warn: #b45309;
        --warn-soft: #fef3c7;
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }
    .hero {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        padding: 1.2rem 1.4rem;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%);
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        margin-bottom: 1.1rem;
    }
    .hero-left { display: flex; gap: 0.9rem; align-items: center; }
    .hero-icon {
        width: 52px; height: 52px; border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 26px; background: var(--brand-soft);
    }
    .hero-title {
        font-size: 1.65rem; font-weight: 800; letter-spacing: -0.02em;
        color: var(--ink); line-height: 1.2;
    }
    .hero-sub { color: var(--muted); font-size: 0.92rem; margin-top: 0.2rem; }
    .hero-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: flex-end; }
    .tag {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em;
        color: var(--brand); background: var(--brand-soft);
        border-radius: 999px; padding: 0.28rem 0.6rem; white-space: nowrap;
    }
    .side-brand {
        display: flex; gap: 0.7rem; align-items: center;
        padding: 0.2rem 0 0.9rem 0; border-bottom: 1px solid var(--line);
        margin-bottom: 0.9rem;
    }
    .side-icon {
        width: 38px; height: 38px; border-radius: 11px;
        display: flex; align-items: center; justify-content: center;
        font-size: 19px; background: var(--brand-soft);
    }
    .side-title { font-weight: 800; color: var(--ink); font-size: 1rem; line-height: 1.25; }
    .side-sub { color: var(--muted); font-size: 0.72rem; margin-top: 0.1rem; }
    .panel {
        border: 1px solid var(--line); border-radius: 14px;
        padding: 1rem 1.1rem; background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
    }
    .panel-title { font-weight: 800; color: var(--ink); margin-bottom: 0.4rem; }
    .muted { color: var(--muted); font-size: 0.88rem; }
    .badge-ok {
        display: inline-block; padding: 0.18rem 0.5rem; border-radius: 999px;
        font-size: 0.72rem; font-weight: 700;
        color: #047857; background: #d1fae5;
    }
    .stChatMessage { border-radius: 14px; }
    div[data-testid="stMetric"] {
        border: 1px solid var(--line); border-radius: 12px;
        padding: 0.6rem 0.8rem; background: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Mock 数据
# ---------------------------------------------------------------------------

DEVICE = {
    "serial": "8F2-1042",
    "model": "X100 空压机",
    "customer": "上海某某食品厂",
    "installed": "2024-03-18",
    "warranty": "在保（至 2027-06-30）",
}

PARTS = [
    {"备件号": "FAN-12038", "名称": "冷却风扇组件", "库存": "上海仓 3 件", "保修": "在保免件费"},
    {"备件号": "FUSE-5A", "名称": "5A 保险", "库存": "上海仓 12 件", "保修": "在保免件费"},
]

WELCOME = (
    "我是**设备售后运维助手**，可以帮你查手册、看实时工况、判断保修和备件，"
    "并把诊断结果整理成可执行的工单草稿。\n\n"
    "你可以直接输入：`X100 报 E-204，出水温度高，客户已停机。`"
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
if "draft_ready" not in st.session_state:
    st.session_state.draft_ready = False
if "work_order_created" not in st.session_state:
    st.session_state.work_order_created = False
if "work_order_id" not in st.session_state:
    st.session_state.work_order_id = ""

# ---------------------------------------------------------------------------
# 逻辑
# ---------------------------------------------------------------------------


def build_response(prompt: str) -> str:
    """Mock 诊断逻辑；真实项目里替换成 AgentChat API 调用。"""
    is_e204 = any(key in prompt for key in ["E-204", "e-204", "高温", "风扇", "停机"])

    if not is_e204:
        return (
            "我可以帮你处理设备售后问题。试试这样问：\n\n"
            "- `X100 报 E-204，出水温度高`\n"
            "- `SN 8F2-1042 还在保修吗？`\n"
            "- `帮我查一下 FAN-12038 的库存`\n\n"
            "如果你提供设备序列号，我会同时查设备档案、实时工况和历史工单。"
        )

    st.session_state.draft_ready = True
    return (
        "### 初步判断\n"
        "E-204 是冷却风扇异常触发的**高温保护**。过去 30 分钟风扇转速为 **0 rpm**，"
        "但控制指令是 **100%**，符合“风扇未转”的特征。\n\n"
        "### 建议排查\n"
        "1. 按手册 §7.3 执行 **LOTO 断电**，确认设备完全停机。\n"
        "2. 检查 **F3 保险**与风扇接插件；若 F3 熔断，更换 5A 保险并检查线束。\n"
        "3. 若风扇卡死，更换风扇组件 **FAN-12038**。\n\n"
        "### 设备与备件\n"
        f"- 设备：{DEVICE['model']}，SN `{DEVICE['serial']}`，{DEVICE['customer']}\n"
        f"- 保修：{DEVICE['warranty']}\n"
        "- 备件：上海仓有 **FAN-12038** 3 件，**FUSE-5A** 12 件\n\n"
        "### 依据\n"
        "- 《X100 Service Manual v3.2》§7.3（p.84）\n"
        "- 服务公告 **SB-2025-11**\n"
        "- 历史工单 **#4831**（同型号 F3 熔断）\n\n"
        "> 已生成工单草稿，去左侧 **「工单草稿」** 确认后即可创建。"
    )


def create_work_order() -> str:
    """Mock 建单；真实项目里替换成 cmms-mcp.create_work_order。"""
    return f"WO-{datetime.now():%Y%m%d}-1031"


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
# 侧边栏
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
    st.caption("演示模式 · Mock 数据")
    st.markdown("**当前设备**")

    serial = st.text_input("设备序列号", value=DEVICE["serial"])
    model = st.selectbox(
        "设备型号",
        ["X100 空压机", "X200 冷水机组", "LabTemp 恒温箱"],
        index=0,
    )

    st.markdown("**能力开关**")
    st.toggle("知识库检索", value=True)
    st.toggle("MCP 工单系统", value=True)
    st.toggle("人工确认后写操作", value=True)

    st.divider()
    st.markdown("**连接状态**")
    st.markdown(
        '<span class="badge-ok">● 知识库</span> '
        '<span class="badge-ok">● CMMS MCP</span> '
        '<span class="badge-ok">● 备件 ERP</span>',
        unsafe_allow_html=True,
    )
    st.caption("当前为界面演示，未连接真实后端。")

    st.divider()
    if st.button("清空对话", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
        st.session_state.draft_ready = False
        st.session_state.work_order_created = False
        st.session_state.work_order_id = ""
        st.rerun()

# ---------------------------------------------------------------------------
# 主区域
# ---------------------------------------------------------------------------

render_header()


def render_chat_page(serial: str, model: str) -> None:
    st.caption(
        f"设备：{model} · SN {serial} · 客户：{DEVICE['customer']} · {DEVICE['warranty']}"
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("描述故障现象，例如：X100 报 E-204，出水温度高，已停机")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("正在查设备档案、实时工况和维修手册..."):
                time.sleep(0.6)
                response = build_response(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    if st.session_state.draft_ready and not st.session_state.work_order_created:
        st.info("工单草稿已生成，去左侧「工单草稿」确认。")


def render_order_page(serial: str, model: str) -> None:
    if not st.session_state.draft_ready:
        st.markdown(
            '<div class="panel"><div class="panel-title">还没有工单草稿</div>'
            '<div class="muted">先在「对话诊断」里描述一个故障，例如 E-204 高温，'
            "助手会自动生成草稿。</div></div>",
            unsafe_allow_html=True,
        )
        return

    if st.session_state.work_order_created:
        st.success(f"工单已创建：{st.session_state.work_order_id}")
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-title">工单已写入 CMMS</div>
              <div class="muted">
                工单号：<b>{st.session_state.work_order_id}</b><br/>
                设备：{model} · SN {serial}<br/>
                优先级：P2 · 预计工时：1.5h<br/>
                预约时间：明天 10:00<br/>
                状态：已派给上海服务组
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("审计记录：设备售后运维助手生成草稿 → 工程师批准 → CMMS MCP 写入")
        return

    st.markdown(
        '<div class="panel"><div class="panel-title">工单草稿 · 待人工确认</div>'
        '<div class="muted">写操作不会自动执行。请核对故障、备件和安全提示后批准。</div></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("优先级", "P2")
    col2.metric("预计工时", "1.5 h")
    col3.metric("建议上门", "明天 10:00")

    st.markdown("**设备与故障**")
    st.markdown(
        f"""
        - 设备：{model} · SN `{serial}`
        - 客户：{DEVICE['customer']}
        - 故障现象：E-204，出水温度 96°C，风扇转速 0 rpm
        - 初步原因：冷却风扇未转 / F3 保险熔断
        - 保修：{DEVICE['warranty']}
        """
    )

    st.markdown("**备件清单**")
    st.dataframe(PARTS, hide_index=True, use_container_width=True)

    st.markdown("**安全提示**")
    st.warning("执行 LOTO 断电并确认零能量后，再检查风扇与保险；禁止带电插拔。")

    with st.form("approve_form"):
        approved = st.checkbox("我已核对信息，同意创建设备售后工单")
        submitted = st.form_submit_button("批准并创建工单", type="primary")

    if submitted:
        if not approved:
            st.warning("请先勾选确认，再创建工单。")
        else:
            with st.spinner("正在通过 CMMS MCP 创建工单..."):
                time.sleep(0.8)
                st.session_state.work_order_id = create_work_order()
                st.session_state.work_order_created = True
            st.rerun()


def render_stack_page() -> None:
    st.markdown("### 这个项目只用 4 + 1 项核心能力")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("知识库文档", "32 份")
    c2.metric("MCP Server", "1 个")
    c3.metric("原生工具", "3 个")
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
                "本项目的实现": "按标题切分 + 元数据过滤 + 页码引用",
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

    st.markdown("### 数据源")
    st.dataframe(
        [
            {"组件": "知识库", "实现": "Chroma + 向量检索", "状态": "演示数据"},
            {"组件": "遥测/保修/备件", "实现": "mock FastAPI + SQLite", "状态": "演示数据"},
            {"组件": "CMMS", "实现": "cmms-mcp", "状态": "演示数据"},
            {"组件": "界面", "实现": "Streamlit（纯 Python）", "状态": "可运行"},
            {"组件": "对话模型", "实现": "DeepSeek / OpenAI 兼容", "状态": "待配置"},
        ],
        hide_index=True,
        use_container_width=True,
    )

    with st.expander("和 AgentChat 是什么关系"):
        st.markdown(
            """
            AgentChat 只作为**参考实现**，不作为项目主体。

            这个简历项目要自己写的是：

            1. `agent.py`：LangChain `create_agent` + 工具注册；
            2. `rag.py`：Chroma 检索 + 页码引用；
            3. `tools.py`：3 个原生工具；
            4. `cmms_server.py`：1 个 FastMCP Server；
            5. `streamlit_app.py`：对话 + 工单审批。

            这样面试时讲的是“我设计的链路”，而不是“我部署了一个平台”。
            """
        )

    st.divider()
    st.markdown(
        "**目标架构**：用户 → Streamlit → FastAPI → LangChain Agent → "
        "RAG / Native Tools / MCP → CMMS、ERP"
    )


if page == "对话诊断":
    render_chat_page(serial, model)
elif page == "工单草稿":
    render_order_page(serial, model)
else:
    render_stack_page()

st.divider()
st.caption(
    "设备售后运维助手 · FieldOps Copilot · 演示界面（Mock 数据） · "
    "正式接入后由 AgentChat 提供 RAG、Tool Calling、MCP 与 HITL 能力"
)
