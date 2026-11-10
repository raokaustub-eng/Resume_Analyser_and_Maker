# ResumeHub — Resume Analyzer and Maker

A student mini project built with Python and Streamlit. It compares a resume with a target job description using explainable skill matching, then builds a clean, editable resume in DOCX or plain text.

## Features

- Scrollable ResumeHub home page with photo-led sections, template previews, career notes, and footer navigation to the builder, analyzer, and theory pages.
- Read text from PDF, DOCX, or TXT resumes, or accept pasted text.
- Find skill overlap against a job description using an editable skill dictionary.
- Show a transparent 100-point checklist, keyword coverage, and practical improvement suggestions.
- Build a resume from typed text and uploaded experience, project, or certification documents; download it as DOCX or TXT.
- Choose Classic, Modern, or Compact single-column DOCX templates.
- Include a Theory & Demo page for the presentation and viva.
- Process the uploaded resume in memory; the app does not intentionally save uploaded files.

The home page includes sign-in and contact UI for demonstration only. No account system or mail service is configured, so the app does not collect credentials or send contact messages. Local photography is stored in `assets/` and sourced from Unsplash.

## Before making it public

The app has no login system, so a public deployment can be used by anyone with its link. Uploaded resume files are sent to the server hosting the app for processing, even though this version does not intentionally save them. Use the included sample resume or other non-sensitive data for a public demo. If you later want people to submit real resumes, first decide how to handle privacy, consent, data retention, and access.

## Run locally

Install Python 3.10 or newer, then open a terminal in this folder and run:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and start the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The browser opens the local app. For a fast demo, copy the text from `sample_resume.txt` and `sample_job_description.txt` into the Analyze page.

## How the score works

| Category | Weight | Method |
| --- | ---: | --- |
| Job-description keywords | 20 | TF-IDF-weighted coverage across filtered terms |
| Target skills | 25 | Matched skills / detected job-description skills |
| Section completeness | 20 | Five common resume sections, four points each |
| Formatting checks | 15 | Length guide, contact details, and date patterns |
| Action verbs | 10 | Two points per distinct detected verb, up to five verbs |
| Measurable results | 10 | Number with a common result unit |

The score is an educational checklist. It is not an ATS score or a hiring prediction. The built-in dictionary is intentionally small; edit `SKILL_ALIASES` in `resume_analyzer.py` to extend it.

## Group of four: suggested ownership

1. **UI and user experience:** `app.py` page flow, styling, forms, and clear messages.
2. **Parsing and analysis:** `resume_analyzer.py` file reading, skill matching, scoring, and suggestions.
3. **Resume generation:** `resume_builder.py` DOCX and TXT output and template decisions.
4. **Integration and presentation:** sample walkthrough, documentation, demo, and limitations.

Each person should understand the overall flow and be ready to explain their part. Agree on the final changes together and run through the demo before presenting.

## Suggested presentation outline (5–7 minutes)

1. **Problem:** People often send the same resume to different roles and struggle to see what evidence is missing.
2. **Goal:** Help users tailor and format their own truthful information.
3. **Architecture:** Streamlit interface → text extraction → rule-based analysis → score and feedback; the builder separately creates DOCX/TXT output.
4. **Live demo:** Analyze the included sample against its target role, review matched/missing skills, then create a resume.
5. **Theory:** Explain whole-word matching and the weighted checklist.
6. **Limitations and future work:** Small skill dictionary, no contextual understanding, no hiring prediction; future options include more industry vocabularies and broader usability testing.

## Example project entry for your own resume

Use only after your group has actually built and presented the app. Adjust the tools and outcomes to match your contribution:

**ResumeHub — Resume Analyzer and Maker | Python, Streamlit, PDF/DOCX processing**

- Built a Python web app that compares resume content with a target job description using explainable skill matching and a weighted feedback checklist.
- Developed an ATS-friendly resume builder that exports user-provided content to editable DOCX and plain-text formats.
- Collaborated in a four-person team to design, implement, and present the application; documented its scoring method, privacy approach, and limitations.

Add numbers such as number of test documents or usability feedback only if you actually collect and verify them. Be ready to describe the part you implemented personally.
