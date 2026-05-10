from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_CANDIDATES = [
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
]


def register_unicode_font() -> tuple[str, str]:
    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            if "GreenLensUnicode" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("GreenLensUnicode", str(font_path)))
            return "GreenLensUnicode", "GreenLensUnicode"
    return FONT_NAME, FONT_BOLD


def build_scan_report(scan) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    font_name, font_bold = register_unicode_font()

    def line(text: str, step: float = 0.7) -> None:
        nonlocal y
        if y < 2 * cm:
            pdf.showPage()
            y = height - 2 * cm
        pdf.drawString(2 * cm, y, text)
        y -= step * cm

    result = scan.result
    pdf.setTitle(f"GreenLens Scan #{scan.id}")
    pdf.setFont(font_bold, 16)
    line(f"GreenLens Scan Report #{scan.id}", 1)

    pdf.setFont(font_name, 11)
    line(f"Status: {'Sick' if result.is_sick else 'Healthy'}")
    line(f"Diagnosis: {result.diagnosis or 'None'}")
    line(f"City: {scan.city or 'N/A'}")
    line(f"Scanned at: {timezone.localtime(scan.scanned_at).strftime('%Y-%m-%d %H:%M')}")

    if scan.temperature is not None and scan.humidity is not None:
        line(f"Weather: {scan.temperature:g} C, {scan.humidity}% humidity")
        line(f"Weather recommendation: {scan.weather_recommendation}")

    line("")
    line("Description:")
    line(result.description or "N/A")

    line("")
    line("Characteristics:")
    for item in result.characteristics:
        line(f"- {item}")

    line("")
    line("Treatment steps:")
    for item in result.treatment_steps:
        line(f"- {item}")

    line("")
    line("Links:")
    for item in result.links:
        line(f"- {item}")

    if scan.image:
        try:
            pdf.drawImage(scan.image.path, 2 * cm, 2 * cm, width=6 * cm, preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
