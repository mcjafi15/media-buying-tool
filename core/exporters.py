# core/exporters.py
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _new_doc(title: str) -> Document:
    doc = Document()
    heading = doc.add_heading(title, 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return doc


def _bold_para(doc, label: str, value: str):
    p = doc.add_paragraph()
    p.add_run(f"{label}: ").bold = True
    p.add_run(value)


def _deal_overview(doc, deal: dict):
    doc.add_heading("Deal Overview", 1)
    _bold_para(doc, "Deal Name", deal["name"])
    _bold_para(doc, "Deal Type", deal["type"].replace("_", " ").title())
    _bold_para(doc, "Location", deal["location"])
    _bold_para(doc, "Campaign Dates", f"{deal['start_date']} to {deal['end_date']}")
    _bold_para(doc, "Target Audience", deal.get("target_audience") or "See notes")


def _to_bytes(doc: Document) -> bytes:
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generate_digital_brief(deal: dict, plan: dict) -> bytes:
    doc = _new_doc(f"Digital Media Brief — {deal['name']}")
    _deal_overview(doc, deal)

    digital = plan["channel_mix"]["digital"]
    doc.add_heading("Digital Budget", 1)
    _bold_para(doc, "Total Digital Budget", f"${digital['usd']:,.0f} ({digital['pct']}% of total)")

    doc.add_heading("Platform Breakdown", 2)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "Platform", "% of Digital", "Est. Budget"
    for platform, pct in digital["breakdown"].items():
        sub = digital["usd"] * pct / 100
        row = table.add_row().cells
        row[0].text = platform.replace("_", " ").title()
        row[1].text = f"{pct}%"
        row[2].text = f"${sub:,.0f}"

    doc.add_heading("Targeting", 1)
    doc.add_paragraph(plan.get("targeting_notes", ""))
    if plan.get("keywords"):
        _bold_para(doc, "Keywords", ", ".join(plan["keywords"]))

    doc.add_heading("Flight Schedule", 1)
    doc.add_paragraph(plan.get("flight_schedule", ""))
    return _to_bytes(doc)


def generate_print_brief(deal: dict, plan: dict) -> bytes:
    doc = _new_doc(f"Print Media Brief — {deal['name']}")
    _deal_overview(doc, deal)

    print_data = plan["channel_mix"]["print"]
    doc.add_heading("Print Budget & Placements", 1)
    _bold_para(doc, "Total Print Budget", f"${print_data['usd']:,.0f} ({print_data['pct']}% of total)")
    _bold_para(doc, "Recommended Publications", print_data.get("notes", ""))
    doc.add_heading("Flight Schedule", 1)
    doc.add_paragraph(plan.get("flight_schedule", ""))
    doc.add_heading("Ad Specifications", 1)
    doc.add_paragraph("Please provide specifications for: full page, half page, and quarter page formats. "
                      "Include bleed dimensions, file format requirements, and submission deadlines.")
    return _to_bytes(doc)


def generate_ooh_brief(deal: dict, plan: dict) -> bytes:
    doc = _new_doc(f"Out-of-Home Media Brief — {deal['name']}")
    _deal_overview(doc, deal)

    ooh = plan["channel_mix"]["ooh"]
    doc.add_heading("OOH Budget & Placements", 1)
    _bold_para(doc, "Total OOH Budget", f"${ooh['usd']:,.0f} ({ooh['pct']}% of total)")
    _bold_para(doc, "Placement Guidance", ooh.get("notes", ""))
    doc.add_heading("Format Requirements", 1)
    doc.add_paragraph("Preferred formats: bulletin (14x48), poster (10.5x36), junior poster (6x12). "
                      "Digital OOH accepted. Provide production specs and posting dates.")
    return _to_bytes(doc)


def generate_rfp_template(deal: dict, plan: dict, vendor_type: str = "print") -> bytes:
    label = vendor_type.upper()
    doc = _new_doc(f"Request for Proposal — {label} — {deal['name']}")

    doc.add_heading("RFP Overview", 1)
    doc.add_paragraph(
        f"Hilco Global is soliciting proposals for {vendor_type} media placements "
        f"in support of the following deal: {deal['name']}."
    )
    _deal_overview(doc, deal)

    budget_key = "print" if vendor_type == "print" else "ooh"
    channel_budget = plan["channel_mix"].get(budget_key, {}).get("usd", 0)
    doc.add_heading("Budget", 1)
    _bold_para(doc, "Available Budget", f"${channel_budget:,.0f}")

    doc.add_heading("Required Deliverables", 1)
    doc.add_paragraph("Please include in your proposal:")
    for item in ["Proposed placement(s) with description", "Audience reach and demographics",
                 "Pricing and production costs", "Creative specifications and deadlines",
                 "Sample placements or media kit"]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("Submission Deadline", 1)
    _bold_para(doc, "Submit by", f"5 business days prior to {deal['start_date']}")
    _bold_para(doc, "Submit to", "[Your Name] — [Your Email]")
    return _to_bytes(doc)


def generate_budget_approval_form(deal: dict, plan: dict) -> bytes:
    doc = _new_doc(f"Media Budget Approval — {deal['name']}")

    doc.add_heading("Deal Information", 1)
    _deal_overview(doc, deal)
    _bold_para(doc, "Total Media Budget Requested", f"${deal['total_budget']:,.0f}")

    doc.add_heading("Channel Allocation", 1)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "Channel", "% of Budget", "Amount"
    for channel, data in plan["channel_mix"].items():
        row = table.add_row().cells
        row[0].text = channel.title()
        row[1].text = f"{data['pct']}%"
        row[2].text = f"${data['usd']:,.0f}"

    doc.add_heading("Rationale", 1)
    doc.add_paragraph(plan.get("rationale", ""))

    doc.add_heading("Approval", 1)
    for label in ["Approved by", "Title", "Date", "Signature"]:
        p = doc.add_paragraph()
        p.add_run(f"{label}: ").bold = True
        p.add_run("_" * 40)
    return _to_bytes(doc)


def generate_media_plan_summary(deal: dict, plan: dict) -> bytes:
    doc = _new_doc(f"Media Plan Summary — {deal['name']}")
    _deal_overview(doc, deal)
    _bold_para(doc, "Total Budget", f"${deal['total_budget']:,.0f}")

    doc.add_heading("Channel Mix", 1)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = "Channel", "%", "Budget", "Notes"
    for channel, data in plan["channel_mix"].items():
        row = table.add_row().cells
        row[0].text = channel.title()
        row[1].text = f"{data['pct']}%"
        row[2].text = f"${data['usd']:,.0f}"
        row[3].text = data.get("notes", "")

    doc.add_heading("Rationale", 1)
    doc.add_paragraph(plan.get("rationale", ""))
    doc.add_heading("Flight Schedule", 1)
    doc.add_paragraph(plan.get("flight_schedule", ""))
    doc.add_heading("Targeting Notes", 1)
    doc.add_paragraph(plan.get("targeting_notes", ""))
    if plan.get("keywords"):
        _bold_para(doc, "Keywords", ", ".join(plan["keywords"]))
    return _to_bytes(doc)
