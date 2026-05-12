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
    (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ),
    (
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ),
    (
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ),
]
LEFT_MARGIN = 2 * cm
RIGHT_MARGIN = 2 * cm
TOP_MARGIN = 2 * cm
BOTTOM_MARGIN = 2 * cm


def register_unicode_font() -> tuple[str, str]:
    for regular_path, bold_path in FONT_CANDIDATES:
        if regular_path.exists():
            if "GreenLensUnicode" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("GreenLensUnicode", str(regular_path)))
            if bold_path.exists() and "GreenLensUnicodeBold" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("GreenLensUnicodeBold", str(bold_path)))
            bold_name = "GreenLensUnicodeBold" if bold_path.exists() else "GreenLensUnicode"
            return "GreenLensUnicode", bold_name
    return FONT_NAME, FONT_BOLD


def wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    if not text:
        return [""]

    lines = []
    for paragraph in str(text).splitlines() or [""]:
        words = paragraph.split(" ")
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            while pdfmetrics.stringWidth(current, font_name, font_size) > max_width and len(current) > 1:
                split_at = len(current)
                for index in range(1, len(current) + 1):
                    if pdfmetrics.stringWidth(current[:index], font_name, font_size) > max_width:
                        split_at = max(1, index - 1)
                        break
                lines.append(current[:split_at])
                current = current[split_at:]
        lines.append(current)
    return lines


def build_scan_report(scan) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - TOP_MARGIN
    font_name, font_bold = register_unicode_font()
    max_width = width - LEFT_MARGIN - RIGHT_MARGIN
    current_font = font_name
    current_size = 11

    def set_font(name: str, size: int) -> None:
        nonlocal current_font, current_size
        current_font = name
        current_size = size
        pdf.setFont(name, size)

    def ensure_space(step: float) -> None:
        nonlocal y
        if y < BOTTOM_MARGIN:
            pdf.showPage()
            y = height - TOP_MARGIN
            pdf.setFont(current_font, current_size)

    def line(text: str, step: float = 0.7) -> None:
        nonlocal y
        for wrapped_line in wrap_text(text, current_font, current_size, max_width):
            ensure_space(step)
            pdf.drawString(LEFT_MARGIN, y, wrapped_line)
            y -= step * cm

    def section(title: str) -> None:
        line("")
        set_font(font_bold, 11)
        line(title)
        set_font(font_name, 11)

    result = scan.result
    pdf.setTitle(f"GreenLens Scan #{scan.id}")
    set_font(font_bold, 16)
    line(f"GreenLens Scan Report #{scan.id}", 1)

    set_font(font_name, 11)
    line(f"Status: {'Sick' if result.is_sick else 'Healthy'}")
    line(f"Diagnosis: {result.diagnosis or 'None'}")
    line(f"City: {scan.city or 'N/A'}")
    line(f"Scanned at: {timezone.localtime(scan.scanned_at).strftime('%Y-%m-%d %H:%M')}")

    if scan.temperature is not None and scan.humidity is not None:
        line(f"Weather: {scan.temperature:g} C, {scan.humidity}% humidity")
        line(f"Weather recommendation: {scan.weather_recommendation}")

    section("Description:")
    line(result.description or "N/A")

    section("Characteristics:")
    for item in result.characteristics:
        line(f"- {item}")

    section("Treatment steps:")
    for item in result.treatment_steps:
        line(f"- {item}")

    section("Links:")
    for item in result.links:
        line(f"- {item}")

    if scan.image:
        try:
            if y < 8 * cm:
                pdf.showPage()
                y = height - TOP_MARGIN
            pdf.drawImage(scan.image.path, LEFT_MARGIN, y - 6 * cm, width=6 * cm, preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
