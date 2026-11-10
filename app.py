from __future__ import annotations

import streamlit as st

from resume_analyzer import analyze_resume, extract_text
from resume_builder import build_resume_docx, resume_as_text


st.set_page_config(page_title="CareerCraft | Resume Studio", page_icon="✦", layout="wide")

st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
      .hero {padding: 2rem 2.2rem; border-radius: 22px; color: white;
        background: linear-gradient(120deg, #13294B 0%, #1D4ED8 65%, #4F8DF7 100%);}
      .hero h1 {font-size: 2.45rem; letter-spacing: -.04em; margin: .2rem 0 .55rem; color: white;}
      .hero p {font-size: 1.06rem; max-width: 760px; color: #E7EEFF; margin-bottom: 0;}
      .eyebrow {text-transform: uppercase; letter-spacing: .14em; font-size: .72rem; font-weight: 700; color: #BFD4FF;}
      .mini-card {background: white; border: 1px solid #E4E9F2; border-radius: 16px; padding: 1rem 1.1rem; min-height: 118px;}
      .mini-card strong {display: block; font-size: 1rem; margin-bottom: .3rem; color: #172033;}
      .mini-card span {color: #667085; font-size: .9rem;}
      .muted {color: #667085;}
      div[data-testid="stMetric"] {background: white; border: 1px solid #E4E9F2; padding: 1rem; border-radius: 14px;}
      .stButton > button, .stDownloadButton > button {border-radius: 10px; font-weight: 650;}
      h2, h3 {letter-spacing: -.02em;}
    </style>
    """,
    unsafe_allow_html=True,
)


def page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="muted">{subtitle}</p>', unsafe_allow_html=True)


def home_page() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">CAREERCRAFT · RESUME STUDIO</div>
          <h1>Make your next application more intentional.</h1>
          <p>Build a clean, readable resume, then check how clearly it speaks to a role. Every suggestion is explainable, and this version does not intentionally store resume uploads.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    cards = st.columns(3)
    for column, title, body in zip(
        cards,
        ("01 · Analyze", "02 · Build", "03 · Improve"),
        (
            "Compare resume skills with a job description and see a transparent score breakdown.",
            "Create a simple, one-column resume and download it as DOCX or plain text.",
            "Get concrete prompts to improve evidence, clarity, and relevance without inventing claims.",
        ),
    ):
        with column:
            st.markdown(f'<div class="mini-card"><strong>{title}</strong><span>{body}</span></div>', unsafe_allow_html=True)

    st.write("")
    st.subheader("A thoughtful resume is specific and easy to scan")
    st.write("Use this tool as a writing aid. It checks for a small set of common skills and resume sections; it cannot predict hiring decisions or replace careful tailoring and proofreading.")
    a, b = st.columns(2)
    with a:
        st.info("**Good bullet pattern**\n\nAction + what you did + how you did it + truthful result.\n\nExample: *Built a Python inventory tracker that reduced weekly stock checks from 2 hours to 30 minutes.*")
    with b:
        st.info("**ATS-friendly by design**\n\nSingle column, standard section headings, selectable text, and no graphics or tables that can confuse resume parsers.")


def analyze_page() -> None:
    page_header("Resume review", "Analyze a resume", "Compare the resume with a target role. The file is read in memory and is not saved by this app.")
    st.info("Privacy for public demos: uploaded resumes are sent to the server hosting this app for processing. This version does not intentionally save them, but use sample or non-sensitive documents until you have added an appropriate privacy notice and reviewed your hosting setup.")
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        uploaded = st.file_uploader("Upload a resume", type=["pdf", "docx", "txt"], help="Text-based PDF, DOCX, or TXT. Scanned-image PDFs may not contain selectable text.")
        pasted_resume = st.text_area("Or paste resume text", height=235, placeholder="Paste the resume text here if you do not want to upload a file.")
    with right:
        job_description = st.text_area("Target job description", height=300, placeholder="Paste the role requirements and responsibilities here. Skill matching uses a small, editable dictionary.")
        st.caption("Tip: paste the full description, then review any suggested missing skills for accuracy.")

    if st.button("Analyze resume", type="primary", use_container_width=True):
        try:
            if pasted_resume.strip():
                resume_text = pasted_resume
            elif uploaded is not None:
                resume_text = extract_text(uploaded.name, uploaded.getvalue())
            else:
                raise ValueError("Upload a resume or paste resume text first.")
            st.session_state.analysis = analyze_resume(resume_text, job_description)
            st.session_state.analysis_error = None
        except Exception as exc:  # Show understandable file and input errors to the user.
            st.session_state.analysis_error = str(exc)
            st.session_state.analysis = None

    if st.session_state.get("analysis_error"):
        st.error(st.session_state.analysis_error)

    result = st.session_state.get("analysis")
    if result:
        st.divider()
        st.subheader("Your review")
        score_col, skills_col, words_col = st.columns(3)
        score_col.metric("Guide score", f"{result['score']} / 100")
        skills_col.metric("Target skills detected", f"{len(result['matched_skills'])} / {len(result['target_skills'])}")
        words_col.metric("Resume length", f"{result['word_count']} words")
        st.caption("The score is a weighted checklist for learning and editing. It is not an ATS score, hiring probability, or assessment of a person's worth.")

        st.subheader("Score breakdown")
        for item in result["categories"]:
            label_col, bar_col, points_col = st.columns([1.5, 3, 0.6], vertical_alignment="center")
            label_col.write(f"**{item['name']}**")
            bar_col.progress(min(1.0, item["score"] / item["max"]))
            points_col.write(f"{item['score']:g}/{item['max']}")
            st.caption(item["detail"])

        good, improve = st.columns(2, gap="large")
        with good:
            st.markdown("#### Skills found in both")
            st.write(", ".join(result["matched_skills"]) if result["matched_skills"] else "No overlap detected by the built-in skill list.")
            st.markdown("#### Other resume skills detected")
            st.write(", ".join(result["resume_skills"]) if result["resume_skills"] else "No terms from the built-in list were detected.")
        with improve:
            st.markdown("#### Skills in the role not found in the resume")
            st.write(", ".join(result["missing_skills"]) if result["missing_skills"] else "No missing listed skills detected.")
            st.markdown("#### Suggestions")
            for suggestion in result["recommendations"]:
                st.write(f"• {suggestion}")


def builder_page() -> None:
    page_header("Resume builder", "Build a clear, ATS-friendly resume", "Fill in only accurate information. The downloaded file uses a simple layout that is easy to edit and scan.")
    with st.form("resume_builder"):
        st.subheader("Contact")
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name *", placeholder="Aarav Sharma")
        email = c2.text_input("Email", placeholder="name@example.com")
        phone = c1.text_input("Phone", placeholder="+91 98765 43210")
        location = c2.text_input("City / region", placeholder="Pune, India")
        linkedin = st.text_input("LinkedIn or portfolio URL", placeholder="linkedin.com/in/yourname")

        st.subheader("Professional story")
        summary = st.text_area("Professional summary", height=95, placeholder="2–3 lines: your current focus, strongest relevant skills, and the kind of work you can contribute.")
        skills = st.text_area("Skills", height=75, placeholder="Python, SQL, Streamlit, communication, ...")
        st.caption("Keep skills truthful and specific. Use terms from the role only when you can back them up with examples.")

        st.subheader("Experience and proof")
        experience = st.text_area("Experience", height=130, placeholder="One line per bullet. Start with an action verb and add scope or a result when you know it. Include role, organization, and dates.")
        projects = st.text_area("Projects", height=130, placeholder="Project name | tools | dates\nBuilt ...\nAdded ...\nMeasured ... (only if measured)")
        education = st.text_area("Education", height=90, placeholder="Degree / program, institution, location, dates. Add relevant coursework or honors only if useful.")
        certifications = st.text_area("Certifications", height=70, placeholder="Certification — Issuer — Year")
        submitted = st.form_submit_button("Create my resume", type="primary", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Add your name before creating the resume.")
        else:
            data = {
                "name": name,
                "email": email,
                "phone": phone,
                "location": location,
                "linkedin": linkedin,
                "summary": summary,
                "skills": skills,
                "experience": experience,
                "projects": projects,
                "education": education,
                "certifications": certifications,
            }
            st.session_state.built_resume = data

    data = st.session_state.get("built_resume")
    if data:
        st.success("Your resume is ready. Open the files and check every detail before you apply.")
        col1, col2 = st.columns(2)
        col1.download_button("Download editable DOCX", build_resume_docx(data), file_name="resume.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary", use_container_width=True)
        col2.download_button("Download plain text", resume_as_text(data), file_name="resume.txt", mime="text/plain", use_container_width=True)
        with st.expander("Preview resume text"):
            st.code(resume_as_text(data), language=None)


def theory_page() -> None:
    page_header("How it works", "The theory behind the tool", "A short explanation your team can use in a class presentation or viva.")
    st.markdown("""
    ### Resume analysis
    The analyzer extracts text from PDF, DOCX, or TXT and compares the resume with a target job description. It uses **rule-based information retrieval**: a dictionary maps common skill spellings to canonical skill names, and whole-word matching identifies terms in each text. It then calculates a weighted checklist score:

    - **40 points — job skill match:** fraction of detected job-description skills also found in the resume.
    - **25 points — section coverage:** five common sections, worth five points each.
    - **15 points — achievement evidence:** action verbs and measurable number patterns.
    - **10 points — length guide:** a broad word-count range, treated as a writing prompt.
    - **10 points — contact details:** presence of an email and phone pattern.

    ### Resume maker
    The builder collects user-written content and creates an editable DOCX and plain-text version. Its layout uses a single column, standard headings, and selectable text, which makes it easier for people and many applicant tracking systems to read. It does not invent a person's background or generate unsupported achievements.

    ### Limits and responsible use
    The skill dictionary is deliberately small and can miss synonyms, context, and skills outside the list. Keyword presence does not prove ability. A resume score cannot predict whether someone will be hired. The guide should help a person notice gaps and improve clarity, while all claims and metrics remain the user's responsibility. The app performs no candidate ranking and does not save uploaded files.
    """)
    st.subheader("Suggested division for a four-person team")
    st.markdown("""
    1. **Frontend and UX:** Streamlit pages, layout, form flow, and accessibility.
    2. **Resume parsing and analyzer:** PDF/DOCX reading, skill dictionary, score breakdown, and recommendations.
    3. **Resume builder:** content fields and DOCX/plain-text generation.
    4. **Integration and presentation:** test scenarios, documentation, demo, and explanation of limitations.
    """)
    st.subheader("A short demo path")
    st.markdown("1. Explain the problem and design goals.  2. Paste a sample resume and job description.  3. Show matched and missing skills plus the score breakdown.  4. Create and download a resume.  5. Explain one limitation and one improvement you would make next.")
    st.subheader("Viva questions to prepare for")
    with st.expander("Why did you use rule-based matching?"):
        st.write("It is easy to explain, runs locally, does not require an API key, and lets us show exactly why a term matched. Its tradeoff is that a small dictionary misses context and synonyms.")
    with st.expander("How is the score calculated?"):
        st.write("It is a weighted checklist: skills 40, sections 25, achievement evidence 15, length 10, and contact details 10. Each component is visible so the user can understand the result.")
    with st.expander("Can the tool guarantee someone will get hired?"):
        st.write("No. Hiring depends on the role, employer, interview, experience, timing, and many other factors. The app only helps make a resume clearer and more tailored.")
    with st.expander("What would you improve next?"):
        st.write("Add a configurable skill dictionary by industry, multilingual parsing, better sentence-level context, accessible template choices, and more user research. A larger model would need careful evaluation and privacy controls.")


with st.sidebar:
    st.markdown("## ✦ CareerCraft")
    st.caption("Resume Studio")
    selected_page = st.radio("Navigate", ["Home", "Analyze", "Build", "Theory & demo"], label_visibility="collapsed")
    st.divider()
    st.caption("No login or database configured")

if selected_page == "Home":
    home_page()
elif selected_page == "Analyze":
    analyze_page()
elif selected_page == "Build":
    builder_page()
else:
    theory_page()
