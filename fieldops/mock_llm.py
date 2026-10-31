"""Deterministic tool-calling model for the offline product-advisor demo."""

from __future__ import annotations

import json
import re
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
BUY_TERMS = ["选型", "怎么选", "试用", "报价", "方案", "联系", "咨询", "采购", "落地", "POC"]


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


def _find_company(text: str) -> str:
    match = re.search(r"(?:公司|客户)[：:]\s*([^\n，,。]{2,30})", text)
    return match.group(1).strip() if match else "某企业客户"


def _find_contact(text: str) -> str:
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    if email:
        return email.group(0)
    phone = re.search(r"1[3-9]\d{9}", text)
    return phone.group(0) if phone else "待补充"


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

    def _final_answer(
        self, messages: list[BaseMessage], lead: dict[str, Any], query: str
    ) -> str:
        knowledge = self._latest(messages, "search_knowledge")
        comparison = self._latest(messages, "compare_products")
        cases = self._latest(messages, "search_cases")
        compat = self._latest(messages, "check_compatibility")
        product_list = self._latest(messages, "list_products")
        results = knowledge.get("results", []) if knowledge else []

        lines: list[str] = []
        if comparison:
            left = comparison["product_a"]
            right = comparison["product_b"]
            lines.append("### 选型建议")
            lines.append(
                f"- **{left['product']}**：{left['one_liner']}  \n"
                f"  适合：{'、'.join(left['workloads'][:4])}"
            )
            lines.append(
                f"- **{right['product']}**：{right['one_liner']}  \n"
                f"  适合：{'、'.join(right['workloads'][:4])}"
            )
            lines.append(f"\n{comparison.get('decision_hint', '')}")
        elif product_list:
            lines.append("### 星环产品线")
            for item in product_list[:8]:
                lines.append(f"- **{item['product']}**：{item['one_liner']}")
        elif results:
            lines.append("### 相关资料")
            lines.append(str(results[0].get("snippet", ""))[:400])
        else:
            lines.append("### 先明确需求")
            lines.append("请补充业务负载、数据量、部署环境和国产化要求，我再给出选型建议。")

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
            lines.append("\n### 依据")
            for item in results[:4]:
                page = f"p.{item['page']}" if item.get("page") else ""
                lines.append(
                    f"- {item.get('title', '')} {item.get('section', '')} "
                    f"{page}（{item.get('doc_id', '')}）"
                )

        if lead:
            lines.append(
                "\n### 下一步\n"
                "可以安排产品试用、方案交流或 POC；报价与具体版本需售前确认。"
            )
            lines.append(
                f"\n> 已生成售前线索草稿 **{lead.get('lead_id')}**，"
                "请在左侧「线索草稿」确认后写入 CRM。"
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
        done = {message.name for message in tool_messages}
        products = _find_products(query)
        industry = _find_industry(full_query)
        wants_compare = len(products) >= 2 or any(
            term in query for term in ["怎么选", "区别", "对比", "vs", "VS"]
        )
        wants_cases = any(term in query for term in ["案例", "客户", "同行业", "实践"])
        wants_compat = any(term in query for term in COMPAT_TERMS)
        buy_intent = any(term in query for term in BUY_TERMS)

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
            if industry and (wants_cases or buy_intent):
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

        if buy_intent and "draft_lead" not in done:
            call = self._call(
                "draft_lead",
                {
                    "company": _find_company(full_query),
                    "industry": industry or "待补充",
                    "contact": _find_contact(full_query),
                    "need": query[:300],
                    "products": products,
                },
            )
            if call:
                return ChatResult(
                    generations=[
                        ChatGeneration(message=AIMessage(content="", tool_calls=[call]))
                    ]
                )

        lead = self._latest(messages, "draft_lead")
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=self._final_answer(messages, lead, query))
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
