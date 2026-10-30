"""Generate small ASCII PDFs used to test the PDF ingestion path.

Run:
    python scripts/generate_pdfs.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "manuals" / "pdf"

DOCS = {
    "x100_manual_p84": {
        "frontmatter": {
            "doc_id": "pdf-x100-manual-7-3",
            "title": "X100 Service Manual (PDF)",
            "model": "X100",
            "doc_type": "manual",
            "version": "v3.2",
            "section": "7.3 Cooling Fan and Overheat Protection",
            "page": "84",
        },
        "body": """7.3 Cooling Fan and Overheat Protection

The X100 compressor trips E-204 when outlet water temperature exceeds 95 C and
the cooling fan feedback is below 50 rpm while the command is above 90 percent.

Check the following items in order:
1. Lock out and tag out (LOTO) the main power.
2. Inspect fan connector XF3 for loose or burnt pins.
3. Measure F3 fuse continuity; replace with a 5 A slow-blow fuse if open.
4. Manually rotate the fan; replace fan assembly FAN-12038 if seized.

Never hot-plug the fan connector. Confirm the fan has stopped before service.""",
    },
    "sb_2025_11_pdf": {
        "frontmatter": {
            "doc_id": "pdf-sb-2025-11",
            "title": "Service Bulletin SB-2025-11 (PDF)",
            "model": "X100",
            "doc_type": "service_bulletin",
            "version": "1.0",
            "section": "E-204 Fan Connector Batch Issue",
            "page": "2",
        },
        "body": """Service Bulletin SB-2025-11

Affected X100 units built between January 2024 and September 2024 may develop
high contact resistance at fan connector XF3 in hot and humid sites.

Recommended action:
1. Inspect XF3 for oxidation, pushed-back pins, or burning.
2. Replace the harness with improved part HARN-XF3-02 when affected.
3. If F3 is open, check fan motor current before replacing the fuse.
4. Record the connector batch number in the work order.""",
    },
    "sop_loto_pdf": {
        "frontmatter": {
            "doc_id": "pdf-sop-loto",
            "title": "LOTO Safety SOP (PDF)",
            "model": "X100",
            "doc_type": "sop",
            "version": "2.1",
            "section": "Lockout Tagout and Zero Energy",
            "page": "3",
        },
        "body": """Lockout Tagout and Zero Energy

Before inspecting the fan, fuse, or electrical connections:
1. Notify the customer and stop the machine.
2. Open the main disconnect and apply a lock and tag.
3. Wait five minutes and verify DC bus voltage is below 36 V.
4. Measure fan terminals with a multimeter.
5. Confirm the fan wheel is completely stopped.

Do not bypass F3. Do not hot-plug the fan connector. Do not remove the fan
before zero energy is verified.""",
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
        path = build_pdf(name, data)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
