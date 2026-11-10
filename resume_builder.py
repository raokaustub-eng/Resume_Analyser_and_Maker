"""Create clean, ATS-friendly resume downloads in DOCX and plain text."""

from __future__ import annotations

from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


def _lines(value: str) -> list[str]:
    return [line.strip().lstrip("•*- ").strip() for line in value.splitlines() if line.strip()]


def resume_as_text(data: dict) -> str:
    lines: list[str] = [data.get("name", "").strip()]
    contact = [data.get(key, "").strip() for key in ("email", "phone", "location", "linkedin")]
    lines.append(" | ".join(item for item in contact if item))
    sections = [
        ("PROFESSIONAL SUMMARY", data.get("summary", "")),
        ("SKILLS", ", ".join(_lines(data.get("skills", "")))),
        ("EXPERIENCE", data.get("experience", "")),
        ("PROJECTS", data.get("projects", "")),
        ("EDUCATION", data.get("education", "")),
        ("CERTIFICATIONS", data.get("certifications", "")),
    ]
    for heading, value in sections:
        if value.strip():
            lines.extend(["", heading])
            lines.extend(_lines(value))
    return "\n".join(line for line in lines if line is not None).strip() + "\n"


def build_resume_docx(data: dict, template: str = "Classic") -> bytes:
    template_styles = {
        "Classic": {"font": "Aptos", "accent": (31, 78, 121), "margin": 0.55, "body_size": 9.5},
        "Modern": {"font": "Arial", "accent": (19, 112, 105), "margin": 0.65, "body_size": 10.0},
        "Compact": {"font": "Calibri", "accent": (68, 78, 88), "margin": 0.42, "body_size": 9.0},
    }
    selected_template = template_styles.get(template, template_styles["Classic"])
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(selected_template["margin"])
    section.bottom_margin = Inches(selected_template["margin"])
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)

    styles = document.styles
    styles["Normal"].font.name = selected_template["font"]
    styles["Normal"].font.size = Pt(selected_template["body_size"])
    styles["Normal"].font.color.rgb = RGBColor(35, 45, 62)
    for style_name in ("Heading 1", "Heading 2"):
        styles[style_name].font.name = selected_template["font"]
        styles[style_name].font.color.rgb = RGBColor(*selected_template["accent"])

    name = document.add_paragraph()
    name.alignment = WD_ALIGN_PARAGRAPH.LEFT if template in {"Modern", "Compact"} else WD_ALIGN_PARAGRAPH.CENTER
    name.paragraph_format.space_after = Pt(2)
    run = name.add_run(data.get("name", "Your Name").strip() or "Your Name")
    run.bold = True
    run.font.name = selected_template["font"]
    run.font.size = Pt(23 if template == "Modern" else 18 if template == "Compact" else 21)
    run.font.color.rgb = RGBColor(23, 32, 51)

    contact = [data.get(key, "").strip() for key in ("email", "phone", "location", "linkedin")]
    contact_line = document.add_paragraph(" | ".join(item for item in contact if item))
    contact_line.alignment = name.alignment
    contact_line.paragraph_format.space_after = Pt(8)
    for run in contact_line.runs:
        run.font.size = Pt(8.5)

    def add_section(title: str, value: str, bullets: bool = False) -> None:
        if not value.strip():
            return
        heading = document.add_paragraph()
        heading.paragraph_format.space_before = Pt(5)
        heading.paragraph_format.space_after = Pt(2)
        title_run = heading.add_run(title.upper())
        title_run.bold = True
        title_run.font.size = Pt(10)
        title_run.font.color.rgb = RGBColor(*selected_template["accent"])
        for line in _lines(value):
            paragraph = document.add_paragraph(style="List Bullet" if bullets else "Normal")
            paragraph.paragraph_format.space_after = Pt(1.5)
            paragraph.paragraph_format.line_spacing = 1.02
            paragraph.add_run(line)

    add_section("Professional Summary", data.get("summary", ""))
    add_section("Skills", ", ".join(_lines(data.get("skills", ""))))
    add_section("Experience", data.get("experience", ""), bullets=True)
    add_section("Projects", data.get("projects", ""), bullets=True)
    add_section("Education", data.get("education", ""), bullets=True)
    add_section("Certifications", data.get("certifications", ""), bullets=True)

    output = BytesIO()
    document.save(output)
    return output.getvalue()
