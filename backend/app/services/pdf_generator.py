from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from pathlib import Path
import io

from app.models.prescription import PrescriptionSession, ConfidenceLevel

NAVY = colors.HexColor("#1F3864")
BLUE = colors.HexColor("#2E75B6")
GREEN = colors.HexColor("#2E7D32")
ORANGE = colors.HexColor("#C55A11")
LIGHT_GREY = colors.HexColor("#F5F5F5")
FLAG_YELLOW = colors.HexColor("#FFF3CD")


def generate_prescription_pdf(session: PrescriptionSession) -> bytes:
    """Returns PDF bytes for a given PrescriptionSession."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    elements = []

    # --- Header ---
    header_style = ParagraphStyle("header", fontSize=20, textColor=NAVY,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER)
    sub_style = ParagraphStyle("sub", fontSize=10, textColor=BLUE,
                               fontName="Helvetica", alignment=TA_CENTER)
    elements.append(Paragraph("QuickRx Voice", header_style))
    elements.append(Paragraph("AI-Assisted Prescription", sub_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    elements.append(Spacer(1, 4*mm))

    # --- Patient + Doctor block ---
    info = session.patient_info
    label = ParagraphStyle("lbl", fontSize=9, fontName="Helvetica-Bold", textColor=NAVY)
    val = ParagraphStyle("val", fontSize=9, fontName="Helvetica")

    info_data = [
        ["Patient:", info.patient_name or "—",   "Doctor:", info.doctor_name or "—"],
        ["Age:",     info.patient_age or "—",    "Clinic:", info.clinic_name or "—"],
        ["Gender:",  info.patient_gender or "—", "Date:",   info.date or "—"],
    ]

    info_table = Table(info_data, colWidths=[25*mm, 65*mm, 25*mm, 55*mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",    (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",    (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("TEXTCOLOR",   (0,0), (0,-1), NAVY),
        ("TEXTCOLOR",   (2,0), (2,-1), NAVY),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BLUE))
    elements.append(Spacer(1, 4*mm))

    # --- Prescription heading ---
    rx_style = ParagraphStyle("rx", fontSize=13, fontName="Helvetica-Bold",
                               textColor=NAVY)
    elements.append(Paragraph("Rx — Prescribed Medications", rx_style))
    elements.append(Spacer(1, 3*mm))

    # --- Drug table ---
    col_headers = ["#", "Drug / Generic Name", "Dose", "Frequency",
                   "Duration", "Route", "Instructions", "Notes"]
    table_data = [col_headers]

    for i, drug in enumerate(session.drugs, 1):
        dose_str = f"{drug.dose or '—'} {drug.dose_unit or ''}".strip()
        note = ""
        if drug.flagged_for_review:
            note = "⚠ Review"
        elif drug.confidence_level == ConfidenceLevel.HIGH:
            note = "✓"

        drug_display = drug.generic_name or drug.drug_name or "—"
        if drug.drug_name and drug.generic_name and drug.drug_name.lower() != drug.generic_name.lower():
            drug_display = f"{drug.generic_name}\n({drug.drug_name})"

        table_data.append([
            str(i),
            drug_display,
            dose_str if dose_str != "—" else "—",
            drug.frequency or "—",
            f"{drug.duration or '—'} {drug.duration_unit or ''}".strip() or "—",
            drug.route or "oral",
            drug.instructions or "—",
            note,
        ])

    col_widths = [8*mm, 42*mm, 22*mm, 25*mm, 18*mm, 18*mm, 28*mm, 12*mm]
    drug_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND",   (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",        (0,0), (0,-1),  "CENTER"),
        ("ALIGN",        (7,0), (7,-1),  "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID",         (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
    ]

    # Highlight flagged rows
    for i, drug in enumerate(session.drugs, 1):
        if drug.flagged_for_review:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), FLAG_YELLOW))
            style_cmds.append(("TEXTCOLOR",  (7, i), (7, i),  ORANGE))

    drug_table.setStyle(TableStyle(style_cmds))
    elements.append(drug_table)
    elements.append(Spacer(1, 5*mm))

    # --- Flagged warning ---
    if session.flagged_count > 0:
        warn_style = ParagraphStyle("warn", fontSize=8, textColor=ORANGE,
                                    fontName="Helvetica-Bold")
        elements.append(Paragraph(
            f"⚠ {session.flagged_count} drug(s) flagged for clinician review "
            f"(low extraction confidence). Please verify before dispensing.",
            warn_style
        ))
        elements.append(Spacer(1, 3*mm))

    # --- Footer ---
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BLUE))
    elements.append(Spacer(1, 3*mm))
    footer_style = ParagraphStyle("footer", fontSize=7, textColor=colors.grey,
                                  fontName="Helvetica", alignment=TA_CENTER)
    elements.append(Paragraph(
        "Generated by QuickRx Voice MVP — AI-assisted, not a substitute for clinical judgment. "
        "Clinician must verify all flagged entries before dispensing.",
        footer_style
    ))

    doc.build(elements)
    return buffer.getvalue()
