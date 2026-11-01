"""Deterministic tool-calling model for the offline product-advisor demo."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult

PRODUCTS = ["ArgoDB", "TDH", "TDC", "Sophon", "StellarDB", "KunDB"]
INDUSTRIES = ["金融", "银行", "政务", "能源", "制造", "交通", "运营商"]
COMPAT_TERMS = ["国产化", "信创", "麒麟", "统信", "鲲鹏", "海光", "兼容"]


def _parse_json(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        return {}
    try:
        value = json.loads(content)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _find_products(text: str) -> list[str]:
    lower = text.lower()
    return [name for name in PRODUCTS if name.lower() in lower]


def _find_industry(text: str) -> str:
    for industry in INDUSTRIES:
        if industry in text:
            return "金融" if industry == "银行" else industry
    return ""


class ProductAdvisorModel(BaseChatModel):
    """Rule-based model that emits realistic product-selection tool calls."""

    bound_tools: list[str] = []
    call_counter: int = 0

    @property
    def _llm_type(self) -> str:
        return "transwarp-product-advisor-mock"

    def bind_tools(self, tools: Any, *, tool_choice: Any = None, **kwargs: Any):
        names = []
        for item in tools:
            if isinstance(item, dict):
                names.append(item.get("name") or item.get("function", {}).get("name", ""))
            else:
                names.append(getattr(item, "name", ""))
        self.bound_tools = [name for name in names if name]
        return self

    def _call(self, name: str, args: dict[str, Any]) -> dict[str, Any] | None:
        if self.bound_tools and name not in self.bound_tools:
            return None
        self.call_counter += 1
        return {
            "name": name,
            "args": args,
            "id": f"call_{name}_{self.call_counter}",
            "type": "tool_call",
        }

    @staticmethod
    def _tool_messages(messages: list[BaseMessage]) -> list[ToolMessage]:
        return [m for m in messages if isinstance(m, ToolMessage)]

    @staticmethod
    def _latest(messages: list[BaseMessage], name: str) -> dict[str, Any]:
        for message in reversed(messages):
            if isinstance(message, ToolMessage) and message.name == name:
                return _parse_json(message.content)
        return {}

    @staticmethod
    def _text(messages: list[BaseMessage]) -> str:
        for message in reversed(messages):
            if isinstance(message, HumanMessage) and message.content:
                return str(message.content)
        return ""

    @staticmethod
    def _clarify() -> str:
        return (
            "### 先确认需求\n"
            "为了给出靠谱的选型建议，请补充三点：\n\n"
            "1. **主要负载**：报表/数仓、实时分析、数据湖、OLTP 交易、图关系、AI 建模？\n"
            "2. **数据量**：GB、TB 还是 PB？\n"
            "3. **部署要求**：私有云/混合云？是否有麒麟、统信、鲲鹏、海光等国产化要求？\n\n"
            "如果先给一个方向：\n"
            "- 报表/数仓/实时分析/HTAP → **ArgoDB**\n"
            "- 数据湖/多模平台/大量组件 → **TDH**\n"
            "- 多租户数据云/平台运营 → **TDC**\n"
            "- 机器学习/知识图谱/隐私计算 → **Sophon**\n"
            "- 反欺诈/资金流向/多层关系 → **StellarDB**\n"
            "- 高并发 OLTP/核心交易 → **KunDB**\n\n"
            "你把行业和负载告诉我，我再给具体对比。"
        )

    def _final_answer(self, messages: list[BaseMessage], query: str) -> str:
        knowledge = self._latest(messages, "search_knowledge")
        comparison = self._latest(messages, "compare_products")
        cases = self._latest(messages, "search_cases")
        compat = self._latest(messages, "check_compatibility")
        product_list = self._latest(messages, "list_products")
        results = knowledge.get("results", []) if knowledge else []
        if knowledge.get("abstained"):
            return (
                "### 知识库未命中\n"
                "知识库中没有找到与这个问题足够相关的内容。"
                "可以补充具体产品名、行业或场景，我再查一次。"
            )

        is_combo_query = "组合" in query or (
            bool(results) and results[0].get("doc_id") == "tw-selection-guide"
        )
        if comparison:
            left = comparison["product_a"]
            right = comparison["product_b"]
            lines = ["### 选型建议"]
            lines.append(
                f"- **{left['product']}**：{left['one_liner']}  \n"
                f"  适合：{'、'.join(left['workloads'][:4])}"
            )
            lines.append(
                f"- **{right['product']}**：{right['one_liner']}  \n"
                f"  适合：{'、'.join(right['workloads'][:4])}"
            )
            lines.append(f"\n{comparison.get('decision_hint', '')}")
            return self._with_footnotes(lines, results, cases, compat, query=query)
        if is_combo_query:
            return self._combination_answer(results)

        lines = []
        if product_list:
            lines.append("### 星环产品线")
            for item in product_list[:8]:
                lines.append(f"- **{item['product']}**：{item['one_liner']}")
        elif results:
            lines.append("### 相关资料")
            lines.append(str(results[0].get("snippet", ""))[:400])
        else:
            lines.append("### 先明确需求")
            lines.append("请补充业务负载、数据量、部署环境和国产化要求，我再给出选型建议。")

        return self._with_footnotes(lines, results, cases, compat, query=query)

    @staticmethod
    def _combination_answer(results: list[dict[str, Any]]) -> str:
        lines = [
            "### 常见组合",
            "- **ArgoDB + TDH**：TDH 做数据湖和多模加工，ArgoDB 做高性能分析。",
            "- **TDH + StellarDB + Sophon**：TDH 做平台底座，StellarDB 做图谱，Sophon 做 AI 建模。",
            "- **TDC + ArgoDB**：TDC 提供多租户数据云，ArgoDB 提供分析型数据库服务。",
            "- **KunDB + ArgoDB**：KunDB 承担交易，ArgoDB 承担分析，形成交易/分析分离。",
            "",
            "### 分析过程",
            "这些组合不是拍脑袋，而是按“谁做底座、谁做分析、谁做图/AI、谁做交易”拆出来的：",
            "1. **数据湖 + 高性能分析**：TDH 负责数据湖、多模加工和实时流；ArgoDB 负责报表、实时分析和 HTAP。",
            "2. **平台 + 图谱 + AI**：TDH 做平台底座，StellarDB 做多层关系图谱，Sophon 做机器学习和知识图谱建模。",
            "3. **多租户 + 分析服务**：TDC 提供多租户数据云和平台运营能力，ArgoDB 以分析型数据库服务对外提供查询。",
            "4. **交易 + 分析**：KunDB 承担高并发 OLTP 交易，ArgoDB 承担分析，避免交易库被分析查询拖垮。",
            "",
            "<!-- SMALL -->",
            "### 回答原则",
            "- 先澄清业务负载，不要一上来就报产品名。",
            "- 不要只推最贵的产品，要说明“为什么不是另一个”。",
            "- 涉及具体版本、兼容性、报价时，明确说“需以官方兼容性列表和售前确认为准”。",
        ]
        if results:
            lines.append("### 依据")
            for item in results[:4]:
                page = f"p.{item['page']}" if item.get("page") else ""
                lines.append(
                    f"- {item.get('title', '')} {item.get('section', '')} "
                    f"{page}（{item.get('doc_id', '')}）"
                )
        return "\n".join(lines)

    @staticmethod
    def _with_footnotes(
        lines: list[str],
        results: list[dict[str, Any]],
        cases: dict[str, Any],
        compat: dict[str, Any],
        query: str = "",
    ) -> str:
        if cases.get("cases"):
            lines.append("\n### 相关案例")
            for case in cases["cases"][:2]:
                lines.append(
                    f"- {case['industry']} · {case['scenario']}（{'、'.join(case['products'])}）"
                )

        if compat:
            lines.append("\n### 兼容性")
            lines.append(
                f"- 操作系统：**{compat.get('os')}**；CPU：**{compat.get('cpu')}**。"
            )
            lines.append(compat.get("note", "具体版本以官方兼容性列表为准。"))

        if results:
            lines.append("\n<!-- SMALL -->")
            lines.append("### 依据")
            for item in results[:4]:
                page = f"p.{item['page']}" if item.get("page") else ""
                lines.append(
                    f"- {item.get('title', '')} {item.get('section', '')} "
                    f"{page}（{item.get('doc_id', '')}）"
                )

        if any(term in query for term in ["报价", "POC", "试用", "方案"]):
            lines.append(
                "\n### 商务流程\n"
                "报价、POC 和试用需要结合数据量、部署环境、产品版本由售前确认；"
                "本演示不提供真实价格承诺。"
            )
        return "\n".join(lines)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        full_query = self._text(messages)
        query = full_query.split("\n\n")[0]
        tool_messages = self._tool_messages(messages)
        products = _find_products(query)
        industry = _find_industry(full_query)
        wants_compare = len(products) >= 2 or any(
            term in query for term in ["怎么选", "区别", "对比", "vs", "VS"]
        )
        wants_cases = any(term in query for term in ["案例", "客户", "同行业", "实践"])
        wants_compat = any(term in query for term in COMPAT_TERMS)
        specific = bool(products) or any(
            term in query
            for term in [
                "怎么选",
                "区别",
                "对比",
                "案例",
                "组合",
                "国产化",
                "兼容",
                "报价",
                "POC",
                "试用",
                "有哪些",
                "产品线",
                "HTAP",
                "OLTP",
                "数据湖",
                "多租户",
                "子产品",
                "存储模型",
                "关系查询",
                "图数据库",
                "迁移",
            ]
        )

        if not specific and not tool_messages:
            return ChatResult(
                generations=[
                    ChatGeneration(message=AIMessage(content=self._clarify()))
                ]
            )

        if not tool_messages:
            calls = []
            call = self._call("search_knowledge", {"query": query[:300]})
            if call:
                calls.append(call)
            if wants_compare and len(products) >= 2:
                call = self._call(
                    "compare_products",
                    {"product_a": products[0], "product_b": products[1]},
                )
                if call:
                    calls.append(call)
            if industry and wants_cases:
                call = self._call(
                    "search_cases",
                    {"industry": industry, "scenario": query[:100]},
                )
                if call:
                    calls.append(call)
            if wants_compat:
                os_name = "麒麟" if "麒麟" in query else (
                    "统信" if "统信" in query else "麒麟"
                )
                cpu = "鲲鹏" if "鲲鹏" in query else (
                    "海光" if "海光" in query else "x86"
                )
                call = self._call(
                    "check_compatibility", {"os_name": os_name, "cpu": cpu}
                )
                if call:
                    calls.append(call)
            if not products and any(term in query for term in ["产品", "有哪些", "产品线"]):
                call = self._call("list_products", {})
                if call:
                    calls.append(call)
            if calls:
                return ChatResult(
                    generations=[
                        ChatGeneration(message=AIMessage(content="", tool_calls=calls))
                    ]
                )

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=self._final_answer(messages, query))
                )
            ]
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
