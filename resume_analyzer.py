"""Transparent, local resume analysis helpers for the student project."""

from __future__ import annotations

import io
import math
import re
from collections import Counter
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

STOP_WORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "our", "that", "the", "their", "this",
    "to", "we", "with", "will", "you", "your",
})
DATE_PATTERN = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+(?:19|20)\d{2}\b|"
    r"\b(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:(?:19|20)?\d{2}|present|current)\b|"
    r"\b(?:19|20)\d{2}\b",
    re.IGNORECASE,
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


def rewrite_bullet(bullet: str, action_verb: str) -> str:
    """Suggest a stronger bullet structure without inventing evidence."""
    allowed_verbs = {
        "built", "created", "designed", "developed", "improved", "implemented",
        "increased", "reduced", "led", "launched", "automated", "analyzed",
        "managed", "delivered", "organized", "resolved", "streamlined",
    }
    selected_verb = action_verb.strip()
    if selected_verb.lower() not in allowed_verbs:
        raise ValueError("Choose an action verb from the provided list.")

    content = bullet.strip().lstrip("•*- ").strip()
    if not content:
        raise ValueError("Select a resume bullet with text first.")

    content = re.sub(
        r"^(?:(?:was|were)\s+)?(?:responsible\s+for|worked\s+(?:on|with)|"
        r"helped\s+(?:with|to)|assisted\s+(?:with|in|on)|participated\s+in)\s+",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"^(?:" + "|".join(re.escape(verb) for verb in ACTION_VERBS) + r")\b\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = content.rstrip(" .;:")
    return f"{selected_verb[0].upper() + selected_verb[1:]} {content}; add a verified result: [verified metric]."


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


def _tfidf_keywords(job_description: str, resume_text: str, limit: int = 16) -> tuple[list[str], list[str], list[str], float]:
    job_tokens = [
        token.strip(".-").lower()
        for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9+#.-]*", job_description)
        if len(token.strip(".-")) > 2 and token.strip(".-").lower() not in STOP_WORDS
    ]
    resume_tokens = [
        token.strip(".-").lower()
        for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9+#.-]*", resume_text)
        if len(token.strip(".-")) > 2 and token.strip(".-").lower() not in STOP_WORDS
    ]
    if not job_tokens:
        return [], [], [], 0.0

    job_counts = Counter(job_tokens)
    resume_terms = set(resume_tokens)
    document_count = 2
    ranked_terms = []
    for term, count in job_counts.items():
        document_frequency = 1 + (term in resume_terms)
        inverse_document_frequency = math.log((1 + document_count) / (1 + document_frequency)) + 1
        weight = (count / len(job_tokens)) * inverse_document_frequency
        ranked_terms.append((term, weight))

    ranked_terms.sort(key=lambda item: (-item[1], item[0]))
    matched_terms = [item for item in ranked_terms if item[0] in resume_terms]
    missing_terms = [item for item in ranked_terms if item[0] not in resume_terms]
    selected_matches = matched_terms[: limit // 2]
    selected_gaps = missing_terms[: limit - len(selected_matches)]
    selected = selected_matches + selected_gaps
    if len(selected) < limit:
        selected.extend(matched_terms[len(selected_matches) : limit - len(selected)])
    selected.sort(key=lambda item: (-item[1], item[0]))
    keywords = [term for term, _ in selected]
    matched = [term for term in keywords if term in resume_terms]
    missing = [term for term in keywords if term not in resume_terms]
    total_weight = sum(weight for _, weight in ranked_terms)
    matched_weight = sum(weight for term, weight in ranked_terms if term in resume_terms)
    score = 20 * matched_weight / total_weight if total_weight else 0.0
    return keywords, matched, missing, round(score, 1)


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
    skill_points = round(25 * len(matched) / len(target_skills), 1) if target_skills else 0.0
    keywords, matched_keywords, missing_keywords, keyword_points = _tfidf_keywords(jd, resume)

    sections = _section_presence(resume)
    section_points = round(20 * sum(sections.values()) / len(sections), 1)

    lowered = resume.lower()
    action_hits = sorted({verb for verb in ACTION_VERBS if re.search(r"(?<![a-z])" + verb + r"(?![a-z])", lowered)})
    has_numbers = re.search(r"\b\d+(?:[.,]\d+)?\s?(?:%|percent|k|m|users|customers|hours|days|weeks|months|years)\b|\b\d+%", lowered) is not None
    action_points = min(10.0, round(len(action_hits) * 2.0, 1))
    measurable_points = 10.0 if has_numbers else 0.0

    word_count = len(re.findall(r"\b[\w+#.-]+\b", resume))
    readability_points, readability_note = _readability_points(word_count)
    has_email = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", resume, re.I) is not None
    has_phone = re.search(r"(?:\+?\d[\d .()\-]{7,}\d)", resume) is not None
    has_dates = DATE_PATTERN.search(resume) is not None
    length_points = readability_points / 2
    contact_points = (2.5 if has_email else 0.0) + (2.5 if has_phone else 0.0)
    date_points = 5.0 if has_dates else 0.0
    formatting_points = length_points + contact_points + date_points

    categories = [
        {"name": "Job-description keywords", "score": keyword_points, "max": 20, "detail": f"{len(matched_keywords)} of {len(keywords)} displayed terms overlap; the score uses TF-IDF-weighted coverage across the full filtered job-description vocabulary."},
        {"name": "Target skills", "score": skill_points, "max": 25, "detail": f"{len(matched)} of {len(target_skills)} listed skills detected in both documents." if target_skills else "No skills from the small built-in dictionary were detected in the job description."},
        {"name": "Section completeness", "score": section_points, "max": 20, "detail": f"{sum(sections.values())} of {len(sections)} common sections detected; each section contributes four points."},
        {"name": "Formatting checks", "score": formatting_points, "max": 15, "detail": f"Length {length_points:g}/5 ({word_count} words; {readability_note.lower()}); contact {contact_points:g}/5 (email {'found' if has_email else 'not found'}, phone {'found' if has_phone else 'not found'}); date format {date_points:g}/5 ({'year/date pattern found' if has_dates else 'no recognizable year/date found'})."},
        {"name": "Action verbs", "score": action_points, "max": 10, "detail": f"{len(action_hits)} distinct verbs detected ({', '.join(action_hits) if action_hits else 'none'}); two points per detected verb, capped at ten."},
        {"name": "Measurable results", "score": measurable_points, "max": 10, "detail": f"{'A number with a common result unit was detected.' if has_numbers else 'No number with a common result unit was detected; add one only when you can verify it.'}"},
    ]

    recommendations: list[str] = []
    if not target_skills:
        recommendations.append("The job description did not contain skills from the built-in dictionary. Add explicit skill terms to the job description or extend SKILL_ALIASES in resume_analyzer.py.")
    if missing_keywords:
        recommendations.append("Review these job-description keywords and add only those you can support with real experience: " + ", ".join(missing_keywords[:8]) + ".")
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
    if not has_dates:
        recommendations.append("Add clear dates to education, projects, or experience where relevant (for example, 2024–2025 or Jan 2025).")
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
        "keywords": keywords,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "resume_skills": resume_skills,
        "target_skills": target_skills,
        "sections": sections,
        "recommendations": recommendations,
        "word_count": word_count,
        "action_verbs": action_hits,
        "has_numbers": has_numbers,
        "has_email": has_email,
        "has_phone": has_phone,
        "has_dates": has_dates,
    }
