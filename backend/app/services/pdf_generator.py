"""
Prescription PDF — designed to look like a real clinic letterhead script,
not a data dump: serif letterhead, patient strip, big ℞, numbered regimen
lines, safety warnings, and a signature block.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io

from app.models.prescription import PrescriptionSession
from app.services.safety import check_interactions

# palette — matches the web app's paper/ink/emerald design system
INK      = colors.HexColor("#14231D")
INK_SOFT = colors.HexColor("#3D4F46")
MUTED    = colors.HexColor("#6B7A71")
ACCENT   = colors.HexColor("#0B7A55")
PAPER    = colors.HexColor("#F6F4EE")
LINE     = colors.HexColor("#D8D4C8")
WARN     = colors.HexColor("#A75A08")
WARN_BG  = colors.HexColor("#FAF0E1")
DANGER   = colors.HexColor("#B3261E")
DANGER_BG = colors.HexColor("#FBEBE9")

S = {
    "clinic":   ParagraphStyle("clinic", fontName="Times-Bold", fontSize=22,
                               textColor=INK, leading=26),
    "doctor":   ParagraphStyle("doctor", fontName="Helvetica", fontSize=10.5,
                               textColor=INK_SOFT, leading=14),
    "date":     ParagraphStyle("date", fontName="Helvetica", fontSize=10,
                               textColor=MUTED, alignment=TA_RIGHT),
    "plabel":   ParagraphStyle("plabel", fontName="Helvetica-Bold", fontSize=7.5,
                               textColor=ACCENT, leading=11),
    "pvalue":   ParagraphStyle("pvalue", fontName="Helvetica", fontSize=10.5,
                               textColor=INK, leading=13),
    "rx":       ParagraphStyle("rx", fontName="Times-BoldItalic", fontSize=30,
                               textColor=INK, leading=34),
    "drugname": ParagraphStyle("drugname", fontName="Times-Bold", fontSize=13,
                               textColor=INK, leading=16),
    "regimen":  ParagraphStyle("regimen", fontName="Helvetica", fontSize=10,
                               textColor=INK_SOFT, leading=14),
    "note":     ParagraphStyle("note", fontName="Helvetica-Oblique", fontSize=9,
                               textColor=MUTED, leading=12),
    "alert":    ParagraphStyle("alert", fontName="Helvetica", fontSize=9,
                               textColor=WARN, leading=12),
    "warnhead": ParagraphStyle("warnhead", fontName="Helvetica-Bold", fontSize=9.5,
                               textColor=DANGER, leading=13),
    "warnline": ParagraphStyle("warnline", fontName="Helvetica", fontSize=9,
                               textColor=INK_SOFT, leading=13),
    "sig":      ParagraphStyle("sig", fontName="Helvetica", fontSize=10,
                               textColor=INK, alignment=TA_RIGHT, leading=14),
    "footer":   ParagraphStyle("footer", fontName="Helvetica", fontSize=7,
                               textColor=MUTED, alignment=TA_CENTER, leading=10),
}


def _dr(name: str | None) -> str:
    if not name:
        return "—"
    return name if name.lower().startswith("dr") else f"Dr. {name}"


def generate_prescription_pdf(session: PrescriptionSession) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=16*mm, bottomMargin=14*mm,
    )
    info = session.patient_info
    el = []

    # ---- Letterhead -------------------------------------------------------
    clinic = info.clinic_name or "QuickRx Voice Clinic"
    head = Table(
        [[Paragraph(clinic, S["clinic"]),
          Paragraph(f"Date<br/><b>{info.date or '—'}</b>", S["date"])],
         [Paragraph(f"{_dr(info.doctor_name)} &nbsp;·&nbsp; Consultation record", S["doctor"]), ""]],
        colWidths=[128*mm, 46*mm],
    )
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    el.append(head)
    el.append(Spacer(1, 4*mm))
    el.append(HRFlowable(width="100%", thickness=1.6, color=INK))
    el.append(Spacer(1, 5*mm))

    # ---- Patient strip ----------------------------------------------------
    def cell(label, value):
        return [Paragraph(label.upper(), S["plabel"]), Paragraph(value or "—", S["pvalue"])]

    strip = Table(
        [[cell("Patient", info.patient_name),
          cell("Age", info.patient_age),
          cell("Sex", info.patient_gender),
          cell("Visit ID", session.session_id[:8])]],
        colWidths=[70*mm, 30*mm, 34*mm, 40*mm],
    )
    strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), 0.75, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    el.append(strip)
    el.append(Spacer(1, 7*mm))

    # ---- Rx mark (the ℞ glyph is missing from the base-14 PDF fonts) ----
    el.append(Paragraph("Rx", S["rx"]))
    el.append(Spacer(1, 2*mm))

    # ---- Regimen lines ----------------------------------------------------
    for i, drug in enumerate(session.drugs, 1):
        name = drug.generic_name or drug.drug_name or "—"
        title = f"{i}.&nbsp;&nbsp;{name}"
        if drug.dose:
            title += f" &nbsp;{drug.dose} {drug.dose_unit or ''}".rstrip()

        parts = []
        if drug.frequency:
            parts.append(drug.frequency)
        if drug.duration:
            parts.append(f"for {drug.duration} {drug.duration_unit or ''}".strip())
        if drug.route and drug.route != "oral":
            parts.append(drug.route)
        regimen = "  ·  ".join(parts) if parts else "—"
        if drug.instructions:
            regimen += f"  ·  <i>{drug.instructions}</i>"

        rows = [[Paragraph(title, S["drugname"])],
                [Paragraph(regimen, S["regimen"])]]
        if drug.dose_alert:
            rows.append([Paragraph(f"&#9888; {drug.dose_alert}", S["alert"])])
        if drug.flagged_for_review and not drug.manually_verified:
            rows.append([Paragraph("&#9888; Low extraction confidence — verify before dispensing.", S["alert"])])

        block = Table(rows, colWidths=[174*mm])
        block.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 3),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
            ("TOPPADDING", (0, 1), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
            ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE),
        ]))
        el.append(block)
        el.append(Spacer(1, 2.5*mm))

    if not session.drugs:
        el.append(Paragraph("No medications recorded.", S["note"]))

    # ---- Safety warnings ----------------------------------------------------
    interactions = check_interactions(session.drugs)
    if interactions:
        el.append(Spacer(1, 4*mm))
        warn_rows = [[Paragraph("&#9888; DRUG INTERACTION ALERTS", S["warnhead"])]]
        for ix in interactions:
            sev = "MAJOR" if ix.severity == "major" else "Moderate"
            warn_rows.append([Paragraph(
                f"<b>{ix.drug_a} + {ix.drug_b}</b> ({sev}): {ix.note}", S["warnline"])])
        warn = Table(warn_rows, colWidths=[174*mm])
        warn.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DANGER_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, DANGER),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        el.append(warn)

    if session.flagged_count > 0:
        el.append(Spacer(1, 3*mm))
        el.append(Paragraph(
            f"&#9888; {session.flagged_count} entr{'y' if session.flagged_count == 1 else 'ies'} "
            f"flagged for clinician review (low extraction confidence).",
            S["alert"]))

    # ---- Signature ----------------------------------------------------------
    el.append(Spacer(1, 18*mm))
    sig = Table(
        [[Paragraph("_______________________", S["sig"])],
         [Paragraph(f"<b>{_dr(info.doctor_name)}</b><br/>Signature &amp; stamp", S["sig"])]],
        colWidths=[174*mm],
    )
    sig.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    el.append(sig)

    # ---- Footer -------------------------------------------------------------
    el.append(Spacer(1, 8*mm))
    el.append(HRFlowable(width="100%", thickness=0.5, color=LINE))
    el.append(Spacer(1, 2*mm))
    el.append(Paragraph(
        "Generated by QuickRx Voice — AI-assisted transcription with clinician verification. "
        "Not valid without signature. Interaction alerts are decision support, not a complete interaction database.",
        S["footer"]))

    doc.build(el)
    return buffer.getvalue()
