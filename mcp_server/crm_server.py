"""CRM MCP server: the external system-of-record boundary."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from fieldops.db import (
    approve_lead,
    create_lead,
    get_by_crm_lead_id,
    get_lead as get_lead_record,
    init_db,
)

mcp = FastMCP(
    "crm",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8765")),
)


@mcp.tool()
def create_lead(
    lead_id: str,
    company: str,
    industry: str,
    contact: str,
    need: str,
    products: list[str] | None = None,
) -> dict:
    """Create a CRM lead from an approved draft.

    Args:
        lead_id: Local draft ID.
        company: Customer company.
        industry: Industry.
        contact: Contact information.
        need: Requirement summary.
        products: Recommended products.
    """

    init_db()
    lead = get_lead_record(lead_id)
    if lead is None:
        lead = create_lead(
            lead_id=lead_id,
            company=company,
            industry=industry,
            contact=contact,
            need=need,
            products=products or [],
        )

    if lead["status"] == "approved" and lead.get("crm_lead_id"):
        return {
            "crm_lead_id": lead["crm_lead_id"],
            "lead_id": lead_id,
            "status": "already_approved",
        }

    crm_lead_id = f"CRM-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:4].upper()}"
    approve_lead(lead_id, crm_lead_id)
    return {
        "crm_lead_id": crm_lead_id,
        "lead_id": lead_id,
        "company": company,
        "industry": industry,
        "products": products or [],
        "status": "approved",
    }


@mcp.tool()
def get_lead(crm_lead_id: str) -> dict:
    """Read a lead from CRM by CRM lead ID."""

    init_db()
    lead = get_by_crm_lead_id(crm_lead_id)
    if not lead:
        return {"error": f"lead {crm_lead_id} not found"}
    return lead


if __name__ == "__main__":
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))  # type: ignore[arg-type]
