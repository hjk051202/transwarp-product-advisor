"""Native LangChain tools used by the FieldOps agent."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from langchain_core.tools import tool

from fieldops.data import get_device, get_part, get_telemetry as load_telemetry
from fieldops.db import create_draft, init_db
from fieldops.rag import search_json

DEFAULT_SAFETY = [
    "执行 LOTO 断电并确认零能量",
    "禁止带电插拔风扇接插件",
    "更换风扇前确认叶轮完全停止",
]


def _dumps(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@tool
def get_telemetry(asset_id: str, minutes: int = 30) -> str:
    """查询设备最近一段时间的实时工况。

    当用户询问设备当前温度、风扇转速、故障码、是否停机时使用。

    Args:
        asset_id: 设备序列号，例如 8F2-1042。
        minutes: 查询最近多少分钟，默认 30。
    """

    data = load_telemetry(asset_id, minutes)
    if not data:
        return _dumps({"error": f"未找到设备 {asset_id} 的遥测数据"})
    return _dumps(data)


@tool
def check_warranty(serial: str) -> str:
    """查询设备保修状态。

    当用户询问是否在保、保修到期时间、能否免费换件时使用。

    Args:
        serial: 设备序列号，例如 8F2-1042。
    """

    device = get_device(serial)
    if not device:
        return _dumps({"error": f"未找到设备 {serial}"})
    return _dumps(
        {
            "serial": device["serial"],
            "model": device["model"],
            "customer": device["customer"],
            "warranty": device["warranty"],
            "warranty_end": device["warranty_end"],
        }
    )


@tool
def check_parts(part_no: str, region: str = "上海") -> str:
    """查询备件库存和价格。

    当用户询问某个备件有没有货、在哪个仓、多少钱时使用。

    Args:
        part_no: 备件号，例如 FAN-12038。
        region: 仓库区域，默认上海。
    """

    part = get_part(part_no)
    if not part:
        return _dumps({"error": f"未找到备件 {part_no}"})
    return _dumps(
        {
            "part_no": part["part_no"],
            "name": part["name"],
            "spec": part["spec"],
            "region": region,
            "stock": part["stock"].get(region, 0),
            "all_stock": part["stock"],
            "price_cny": part["price_cny"],
            "warranty_covered": part["warranty_covered"],
        }
    )


@tool
def search_knowledge(query: str) -> str:
    """检索设备手册、服务公告、SOP 和历史工单。

    当需要故障码解释、排查步骤、安全规范或相似案例时使用。
    返回结果包含 doc_id、页码和原文片段，回答时必须引用。

    Args:
        query: 检索关键词，例如 E-204 高温 风扇。
    """

    return search_json(query, k=4)


@tool
def draft_work_order(
    asset_id: str,
    title: str,
    description: str,
    priority: str = "P2",
    parts: list[str] | None = None,
    scheduled_at: str | None = None,
) -> str:
    """生成工单草稿，但不写入 CMMS。

    当已经完成诊断、需要把故障、备件和安全提示整理成工单时使用。
    该工具只写本地 draft 表，必须由工程师在界面上确认后才能正式建单。

    Args:
        asset_id: 设备序列号。
        title: 工单标题。
        description: 故障现象、判断依据和处理建议。
        priority: 优先级，P1/P2/P3，默认 P2。
        parts: 需要携带的备件号列表。
        scheduled_at: 建议上门时间，ISO 格式或自然语言描述。
    """

    init_db()
    parts = parts or []
    if not scheduled_at:
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).strftime(
            "%Y-%m-%d 10:00"
        )
    draft_id = f"DRF-{datetime.now():%Y%m%d%H%M%S}-{uuid4().hex[:4]}"
    draft = create_draft(
        draft_id=draft_id,
        asset_id=asset_id,
        title=title,
        description=description,
        priority=priority,
        parts=parts,
        safety=DEFAULT_SAFETY,
        scheduled_at=scheduled_at,
    )
    return _dumps(draft)


NATIVE_TOOLS = [
    search_knowledge,
    get_telemetry,
    check_warranty,
    check_parts,
    draft_work_order,
]
