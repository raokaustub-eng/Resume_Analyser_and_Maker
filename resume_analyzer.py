"""Transparent, local resume analysis helpers for the student project."""

from __future__ import annotations

import io
import re
from collections.abc import Iterable

from docx import Document
from pypdf import PdfReader


# Canonical skill names mapped to common spellings. This small, explainable
# dictionary is intentionally editable by students; it is not an AI model.
SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "Java": ("java",),
    "C++": ("c++", "cpp"),
    "C#": ("c#", "c sharp"),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript",),
    "SQL": ("sql",),
    "HTML": ("html",),
    "CSS": ("css",),
    "React": ("react", "react.js"),
    "Node.js": ("node.js", "nodejs"),
    "Flask": ("flask",),
    "Django": ("django",),
    "Streamlit": ("streamlit",),
    "Machine learning": ("machine learning", "ml"),
    "Data analysis": ("data analysis", "data analytics"),
    "Excel": ("excel", "microsoft excel"),
    "Power BI": ("power bi",),
    "Tableau": ("tableau",),
    "Git": ("git",),
    "GitHub": ("github",),
    "REST API": ("rest api", "restful api"),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure", "microsoft azure"),
    "Communication": ("communication", "presentation skills"),
    "Leadership": ("leadership", "team leadership"),
    "Project management": ("project management",),
    "Problem solving": ("problem solving", "problem-solving"),
    "Agile": ("agile", "scrum"),
    "Customer service": ("customer service", "client support"),
}

SECTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "Summary": (r"\b(summary|professional profile|objective)\b",),
    "Experience": (r"\b(experience|employment|work history)\b",),
    "Education": (r"\b(education|academic background)\b",),
    "Skills": (r"\b(skills|technical skills|core competencies)\b",),
    "Projects": (r"\b(projects|selected projects|academic projects)\b",),
}

ACTION_VERBS = (
    "built", "created", "designed", "developed", "improved", "implemented",
    "increased", "reduced", "led", "launched", "automated", "analyzed",
    "managed", "delivered", "organized", "resolved", "streamlined",
)


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Read PDF, DOCX, or plain-text resume bytes without saving the file."""
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    elif suffix == "docx":
        document = Document(io.BytesIO(file_bytes))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        table_text = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
        text = "\n".join(paragraphs + table_text)
    elif suffix in {"txt", "text"}:
        text = file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError("Please upload a PDF, DOCX, or TXT file.")

    text = text.strip()
    if not text:
        raise ValueError("No readable text was found. If this is a scanned PDF, try a text-based PDF or paste the resume text.")
    return text


def _has_phrase(text: str, phrase: str) -> bool:
    # Alphanumeric boundaries prevent Java matching JavaScript, while still
    # allowing punctuation such as C++ and Node.js in a resume.
    pattern = r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def find_skills(text: str) -> list[str]:
    return [
        skill
        for skill, aliases in SKILL_ALIASES.items()
        if any(_has_phrase(text, alias) for alias in aliases)
    ]


def _section_presence(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        name: any(re.search(pattern, lowered) for pattern in patterns)
        for name, patterns in SECTION_PATTERNS.items()
    }


def _readability_points(word_count: int) -> tuple[float, str]:
    # A simple length signal for an early-career resume. It is guidance, not a
    # universal hiring rule; experience level and country can change the ideal.
    if 250 <= word_count <= 900:
        return 10.0, "Length is within the guide's broad 250–900 word range."
    if 150 <= word_count < 250 or 900 < word_count <= 1200:
        return 6.0, "Length is a little outside the guide's broad 250–900 word range."
    return 2.0, "Length is far from the guide's broad 250–900 word range; review for useful detail and concision."


def analyze_resume(resume_text: str, job_description: str) -> dict:
    """Return a weighted score and evidence-based feedback for one resume."""
    resume = re.sub(r"\s+", " ", resume_text).strip()
    jd = job_description.strip()
    if len(resume) < 40:
        raise ValueError("Please provide more resume text so the analysis has enough evidence.")
    if len(jd) < 20:
        raise ValueError("Add a job description with at least a few sentences for a meaningful match.")

    resume_skills = find_skills(resume)
    target_skills = find_skills(jd)
    matched = [skill for skill in target_skills if skill in resume_skills]
    missing = [skill for skill in target_skills if skill not in resume_skills]
    skill_points = round(40 * len(matched) / len(target_skills), 1) if target_skills else 0.0

    sections = _section_presence(resume)
    section_points = round(25 * sum(sections.values()) / len(sections), 1)

    lowered = resume.lower()
    action_hits = sorted({verb for verb in ACTION_VERBS if re.search(r"(?<![a-z])" + verb + r"(?![a-z])", lowered)})
    has_numbers = re.search(r"\b\d+(?:[.,]\d+)?\s?(?:%|percent|k|m|users|customers|hours|days|weeks|months|years)\b|\b\d+%", lowered) is not None
    achievement_points = (7.5 if action_hits else 0.0) + (7.5 if has_numbers else 0.0)

    word_count = len(re.findall(r"\b[\w+#.-]+\b", resume))
    readability_points, readability_note = _readability_points(word_count)
    has_email = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", resume, re.I) is not None
    has_phone = re.search(r"(?:\+?\d[\d .()\-]{7,}\d)", resume) is not None
    contact_points = (5.0 if has_email else 0.0) + (5.0 if has_phone else 0.0)

    categories = [
        {"name": "Job skill match", "score": skill_points, "max": 40, "detail": f"{len(matched)} of {len(target_skills)} skills detected from the job description are also detected in the resume." if target_skills else "No skills from the guide's small built-in dictionary were detected in the job description."},
        {"name": "Section coverage", "score": section_points, "max": 25, "detail": f"{sum(sections.values())} of {len(sections)} common sections detected."},
        {"name": "Achievement evidence", "score": achievement_points, "max": 15, "detail": f"{len(action_hits)} distinct action verbs and {'some' if has_numbers else 'no'} measurable number evidence detected."},
        {"name": "Length guide", "score": readability_points, "max": 10, "detail": f"{word_count} words. {readability_note}"},
        {"name": "Contact details", "score": contact_points, "max": 10, "detail": f"Email {'found' if has_email else 'not detected'}; phone {'found' if has_phone else 'not detected'}."},
    ]

    recommendations: list[str] = []
    if not target_skills:
        recommendations.append("The job description did not contain skills from the built-in dictionary. Add explicit skill terms to the job description or extend SKILL_ALIASES in resume_analyzer.py.")
    if missing:
        recommendations.append("If you truly have these qualifications, add evidence for: " + ", ".join(missing) + ". Never add a skill you cannot discuss or demonstrate.")
    absent_sections = [name for name, present in sections.items() if not present]
    if absent_sections:
        recommendations.append("Consider adding clearly labeled sections for: " + ", ".join(absent_sections) + ".")
    if not action_hits:
        recommendations.append("Start experience and project bullets with specific action verbs, such as Built, Analyzed, Led, or Improved.")
    if not has_numbers:
        recommendations.append("Where accurate, quantify outcomes (for example, time saved, records processed, or team size). Do not invent metrics.")
    if not has_email or not has_phone:
        recommendations.append("Check that your preferred email and phone number are easy to find at the top of the resume.")
    if word_count > 900:
        recommendations.append("Review for repetition and keep the most relevant evidence for this particular role.")
    if not recommendations:
        recommendations.append("The main checks look good. Tailor the wording to the role and proofread names, dates, and claims before applying.")

    score = round(sum(category["score"] for category in categories))
    return {
        "score": score,
        "categories": categories,
        "matched_skills": matched,
        "missing_skills": missing,
        "resume_skills": resume_skills,
        "target_skills": target_skills,
        "sections": sections,
        "recommendations": recommendations,
        "word_count": word_count,
        "action_verbs": action_hits,
        "has_numbers": has_numbers,
    }
