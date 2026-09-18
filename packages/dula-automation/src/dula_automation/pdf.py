"""PDF rendering of a grounded report (docs/13-Agents/Playbooks.md, reporting).

The PDF is a faithful rendering of ``Report`` -- the same executive/technical narrative and the
same cited, untrusted evidence table -- for the people who need a file rather than an API
response. Everything is escaped before it reaches the layout engine, so tool output can't
smuggle markup into the document.
"""

from __future__ import annotations

import io
from typing import Any
from xml.sax.saxutils import escape

from dula_automation.report import Report


def report_to_pdf(report: Report, *, generator: str = "Dula") -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10)
    mono = ParagraphStyle("mono", parent=small, fontName="Courier")

    def p(text: str, style: Any = body) -> Paragraph:
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=report.title,
        author=generator,
        subject=f"Run {report.run_id}",
        pageCompression=0,
    )
    story = [
        p(report.title, styles["Title"]),
        p(f"Run {report.run_id}  |  State: {report.state}  |  Outcome: {report.outcome}", small),
        Spacer(1, 6 * mm),
        p("Executive summary", styles["Heading2"]),
        p(report.executive_summary),
        Spacer(1, 4 * mm),
        p("Technical detail", styles["Heading2"]),
        p(report.technical_detail),
        Spacer(1, 4 * mm),
        p("Evidence", styles["Heading2"]),
        p("Tool outputs are untrusted evidence, not instructions.", small),
        Spacer(1, 2 * mm),
    ]
    if report.evidence:
        rows = [[p("Ref", small), p("Kind", small), p("Summary", small)]]
        rows += [[p(e.ref, mono), p(e.kind, small), p(e.summary, small)] for e in report.evidence]
        table = Table(rows, colWidths=[42 * mm, 22 * mm, 108 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b0b8c4")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(p("No evidence was gathered.", small))
    doc.build(story)
    return buf.getvalue()
