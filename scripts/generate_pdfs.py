"""Generate small ASCII PDFs for the PDF ingestion demo.

Run:
    python scripts/generate_pdfs.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "knowledge" / "pdf"

DOCS = {
    "argodb_overview": {
        "frontmatter": {
            "doc_id": "pdf-argodb",
            "title": "Transwarp ArgoDB Overview (PDF)",
            "product": "ArgoDB",
            "doc_type": "product",
            "version": "public-2026",
            "section": "Analytical Database and HTAP",
            "page": "1",
        },
        "body": """Transwarp ArgoDB Overview

ArgoDB is a distributed analytical database for enterprise data warehousing,
real-time analytics and HTAP workloads. It supports standard SQL, lakehouse
architecture, multi-model data and elastic scaling.

Typical scenarios:
- Enterprise data warehouse and BI reporting
- Real-time dashboards and risk analytics
- HTAP with high-concurrency point queries
- Disaster recovery and multi-tenant platforms

If the customer mainly needs a platform-level data lake with many components,
evaluate TDH. If the workload is high-concurrency OLTP, evaluate KunDB.""",
    },
    "tdh_overview": {
        "frontmatter": {
            "doc_id": "pdf-tdh",
            "title": "Transwarp Data Hub Overview (PDF)",
            "product": "TDH",
            "doc_type": "product",
            "version": "public-2026",
            "section": "One-stop Big Data Platform",
            "page": "1",
        },
        "body": """Transwarp Data Hub Overview

TDH is a one-stop big data platform covering data lake, data warehouse,
real-time streaming and multi-model storage. It provides 10 storage engines and
11 data models, with unified SQL and a unified compute engine.

Typical scenarios:
- Enterprise data lake and lakehouse
- Multi-model analytics across relational, graph, search, time-series data
- Real-time streaming and data warehouse
- Platform-level big data foundation with operations tooling

If the customer only needs an analytical database, ArgoDB is more focused.
If the customer wants a multi-tenant data cloud, evaluate TDC.""",
    },
}


def build_pdf(name: str, data: dict) -> Path:
    path = PDF_DIR / f"{name}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "---")
    y -= 14
    for key, value in data["frontmatter"].items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 12
    c.drawString(50, y, "---")
    y -= 22

    c.setFont("Helvetica", 10)
    for paragraph in data["body"].split("\n"):
        for line in textwrap.wrap(paragraph, width=92) or [""]:
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 50
            c.drawString(50, y, line)
            y -= 14
        y -= 4
    c.save()
    return path


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in DOCS.items():
        print(f"wrote {build_pdf(name, data).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
