from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from resume_analyzer import ACTION_VERBS, analyze_resume, extract_text, rewrite_bullet
from resume_builder import build_resume_docx, resume_as_text


st.set_page_config(page_title="ResumeHub | Career Studio", page_icon="✦", layout="wide")
st.session_state.setdefault("dark_mode", False)
st.session_state.setdefault("selected_page", "Home")
st.session_state.setdefault("resume_template", "Classic")

ASSET_DIR = Path(__file__).resolve().parent / "assets"
HERO_IMAGE_BASE64 = base64.b64encode((ASSET_DIR / "hero-writing.jpg").read_bytes()).decode("ascii")

active_dark_mode = st.session_state["dark_mode"]
active_palette = {
    "background": "#111111" if active_dark_mode else "#FFF9DC",
    "surface": "#1C1C1C" if active_dark_mode else "#FFFFFF",
    "sidebar": "#090909" if active_dark_mode else "#FFF1A8",
    "text": "#FFF8D7" if active_dark_mode else "#18150A",
    "muted": "#C7BE9A" if active_dark_mode else "#665A32",
    "border": "#4A421B" if active_dark_mode else "#E7D57B",
    "input": "#242424" if active_dark_mode else "#FFFFFF",
    "accent": "#FFD22E" if active_dark_mode else "#F2C300",
    "accent_text": "#FFD22E" if active_dark_mode else "#725600",
        "guidance_background": "#FFFFFF",
        "guidance_text": "#000000" if active_dark_mode else "#1B2926",
        "guidance_weight": "700" if active_dark_mode else "400",
}

st.markdown(
        f"""
        <style>
            :root {{
                color-scheme: {"dark" if active_dark_mode else "light"};
                --cc-background: {active_palette["background"]};
                --cc-surface: {active_palette["surface"]};
                --cc-sidebar: {active_palette["sidebar"]};
                --cc-text: {active_palette["text"]};
                --cc-muted: {active_palette["muted"]};
                --cc-border: {active_palette["border"]};
                --cc-input: {active_palette["input"]};
                --cc-accent: {active_palette["accent"]};
                --cc-accent-text: {active_palette["accent_text"]};
                --cc-guidance-background: {active_palette["guidance_background"]};
                --cc-guidance-text: {active_palette["guidance_text"]};
                --cc-guidance-weight: {active_palette["guidance_weight"]};
            }}
            html, body, .stApp, [data-testid="stAppViewContainer"] {{background-color: var(--cc-background); color: var(--cc-text);}}
            [data-testid="stHeader"] {{background-color: var(--cc-background);}}
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{background-color: var(--cc-sidebar);}}
            h1, h2, h3, h4, p, li, label, .stMarkdown, .stText, .stRadio {{color: var(--cc-text);}}
            [data-testid="stCaptionContainer"], .muted {{color: var(--cc-muted);}}
            .block-container {{max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}}
            .hero {{background: #111; border-bottom: 5px solid var(--cc-accent); border-radius: 8px; color: white; padding: 2rem 2.2rem;}}
            .hero h1 {{font-size: 2.45rem; letter-spacing: -.04em; margin: .2rem 0 .55rem; color: white;}}
            .hero p {{font-size: 1.06rem; max-width: 760px; color: #E7EEFF; margin-bottom: 0;}}
            .eyebrow {{text-transform: uppercase; letter-spacing: .14em; font-size: .72rem; font-weight: 700; color: var(--cc-accent-text);}}
            .mini-card {{background: var(--cc-surface); border: 1px solid var(--cc-border); border-radius: 8px; padding: 1rem 1.1rem; min-height: 118px;}}
            .mini-card strong {{display: block; font-size: 1rem; margin-bottom: .3rem; color: var(--cc-text);}}
            .mini-card span {{color: var(--cc-muted); font-size: .9rem;}}
            .guidance-panel {{background: var(--cc-guidance-background); border: 1px solid var(--cc-border); border-radius: 8px; color: var(--cc-guidance-text); font-weight: var(--cc-guidance-weight); line-height: 1.55; padding: 1rem;}}
            .guidance-panel strong, .guidance-panel p {{color: var(--cc-guidance-text); font-weight: inherit;}}
            .guidance-panel strong {{font-weight: 800;}}
            .guidance-panel p {{margin: .45rem 0 0;}}
            .career-nav {{align-items: center; display: flex; justify-content: space-between; margin: .2rem 0 1.2rem;}}
            .career-brand {{color: var(--cc-text); font-size: 1.25rem; font-weight: 800;}}
            .career-nav-links {{display: flex; flex-wrap: wrap; gap: 1.25rem; justify-content: center;}}
            .career-nav-links a, .hero-scroll-link {{color: var(--cc-text); font-weight: 700; text-decoration: none;}}
            .career-nav-links a:hover, .hero-scroll-link:hover {{text-decoration: underline;}}
            .landing-hero {{align-items: flex-end; background-position: center 48%; background-size: cover; border-radius: 12px; display: flex; min-height: 430px; overflow: hidden; padding: 2.5rem; position: relative;}}
            .landing-hero::before {{background: rgba(8, 20, 24, .58); content: ""; inset: 0; position: absolute;}}
            .landing-hero-content {{animation: rise-in .7s ease-out both; max-width: 720px; position: relative; z-index: 1;}}
            .landing-hero h1 {{color: #fff; font-family: Georgia, serif; font-size: 3.2rem; line-height: 1.05; margin: .8rem 0 1rem;}}
            .landing-hero p {{color: #F1F4F2; font-size: 1.08rem; line-height: 1.55; max-width: 580px;}}
            .landing-hero .hero-kicker {{color: var(--cc-accent); font-size: .78rem; font-weight: 800; text-transform: uppercase;}}
            .landing-hero .hero-scroll-link {{border-bottom: 2px solid var(--cc-accent); color: var(--cc-accent) !important; display: inline-block; margin-top: .6rem; padding-bottom: .2rem; text-decoration: none;}}
            .landing-section {{padding: 3.2rem 0 1.2rem; scroll-margin-top: 1rem;}}
            .section-kicker {{color: var(--cc-accent-text); font-size: .76rem; font-weight: 800; text-transform: uppercase;}}
            .feature-strip {{border-bottom: 1px solid var(--cc-border); border-top: 1px solid var(--cc-border); margin: 2rem 0 .4rem; padding: 1.3rem 0;}}
            .feature-strip strong {{color: var(--cc-text); display: block; margin-bottom: .3rem;}}
            .feature-strip span {{color: var(--cc-muted); font-size: .92rem;}}
            .template-paper {{background: #fff; border: 1px solid #D7D1B5; box-shadow: 0 12px 30px rgba(0, 0, 0, .1); color: #171717; margin: .35rem 0 1rem; min-height: 245px; padding: 1.15rem; transition: transform .2s ease, box-shadow .2s ease;}}
            .template-paper:hover {{box-shadow: 0 16px 34px rgba(0, 0, 0, .17); transform: translateY(-4px);}}
            .template-paper .paper-name {{border-bottom: 2px solid #E3B600; color: #111; font: 700 1rem Georgia, serif; padding-bottom: .5rem;}}
            .template-paper.classic .paper-name {{text-align: center;}}
            .template-paper.compact {{font-family: Arial, sans-serif; padding: .8rem;}}
            .template-paper.compact .paper-name {{font-family: Arial, sans-serif; font-size: .9rem;}}
            .template-paper.modern .paper-name {{border-color: #E3B600; font-family: Arial, sans-serif; font-size: 1.15rem;}}
            .paper-contact {{color: #66736F; font-size: .58rem; margin: .45rem 0 .8rem; text-align: center;}}
            .paper-section {{color: #725600; font-size: .58rem; font-weight: 800; margin: .6rem 0 .24rem;}}
            .paper-lines {{background: repeating-linear-gradient(to bottom, #CAD2CF 0 1px, transparent 1px 9px); height: 24px; opacity: .8;}}
            .resource-image img {{aspect-ratio: 1.65; border-radius: 8px; object-fit: cover;}}
            .resource-meta {{color: var(--cc-accent-text); font-size: .74rem; font-weight: 800; text-transform: uppercase;}}
            .resource-title {{color: var(--cc-text); font-size: 1.2rem; font-weight: 750; margin: .3rem 0;}}
            .career-footer {{border-top: 1px solid var(--cc-border); color: var(--cc-muted); margin-top: 3rem; padding: 1.4rem 0 .5rem;}}
            .career-footer strong {{color: var(--cc-text);}}
            .career-footer a {{color: var(--cc-accent-text);}}
            @keyframes rise-in {{from {{opacity: 0; transform: translateY(16px);}} to {{opacity: 1; transform: translateY(0);}}}}
            div[data-testid="stMetric"] {{background: var(--cc-surface); border: 1px solid var(--cc-border); padding: 1rem; border-radius: 8px;}}
            div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {{color: var(--cc-text);}}
            .stTextInput input, .stTextArea textarea, .stNumberInput input, [data-baseweb="select"] > div {{background-color: var(--cc-input); color: var(--cc-text); border-color: var(--cc-border);}}
               [data-testid="stAlert"] {{background-color: var(--cc-surface); border: 1px solid var(--cc-border); color: var(--cc-text);}}
               [data-testid="stAlert"] p, [data-testid="stAlert"] strong {{color: var(--cc-text);}}
               [data-testid="stExpander"] {{border-color: var(--cc-border);}}
            [data-testid="stFileUploaderDropzone"] {{background-color: var(--cc-surface); border-color: var(--cc-border);}}
            hr {{border-color: var(--cc-border);}}
            .stButton > button, .stDownloadButton > button {{border-radius: 10px; font-weight: 650;}}
            .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{background: var(--cc-accent); border-color: var(--cc-accent); color: #111;}}
            .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{background: #E2B400; border-color: #E2B400; color: #111;}}
            [data-testid="stRadio"] input {{accent-color: var(--cc-accent);}}
            a:not(.hero-scroll-link) {{color: var(--cc-accent-text);}}
            h2, h3 {{letter-spacing: -.02em;}}
            @media (max-width: 640px) {{
                .block-container {{padding-top: 1rem; padding-bottom: 1.5rem;}}
                .hero {{padding: 1.35rem; border-radius: 12px;}}
                .hero h1 {{font-size: 1.8rem;}}
                .landing-hero {{min-height: 390px; padding: 1.4rem;}}
                .landing-hero h1 {{font-size: 2.25rem;}}
                .landing-section {{padding-top: 2.2rem;}}
                .career-nav {{align-items: flex-start; flex-wrap: wrap; gap: .75rem;}}
                .career-nav-links {{gap: .75rem; justify-content: flex-start;}}
            }}
            @media (prefers-reduced-motion: reduce) {{
                *, *::before, *::after {{animation-duration: .01ms !important; scroll-behavior: auto !important; transition-duration: .01ms !important;}}
            }}
        </style>
        """,
        unsafe_allow_html=True,
)


def page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="muted">{subtitle}</p>', unsafe_allow_html=True)


def navigate_to(page: str, template: str | None = None) -> None:
    if template:
        st.session_state["resume_template"] = template
    st.session_state["selected_page"] = page


def guidance_panel(title: str, body: str) -> None:
    st.markdown(
        f'<div class="guidance-panel"><strong>{html.escape(title)}</strong><p>{body}</p></div>',
        unsafe_allow_html=True,
    )


def render_keyword_badges(label: str, keywords: list[str], color: str, background: str) -> None:
    st.markdown(f"**{label}**")
    if not keywords:
        st.caption("None detected")
        return
    badges = " ".join(
        f'<span style="display:inline-block;margin:0 .35rem .4rem 0;padding:.22rem .5rem;'
        f'border-radius:4px;color:{color};background:{background};font-size:.88rem">{html.escape(word)}</span>'
        for word in keywords
    )
    st.markdown(badges, unsafe_allow_html=True)


def render_highlighted_resume(resume_text: str, keywords: list[str], dark_mode: bool = False) -> None:
    distinct_keywords = sorted(set(keywords), key=len, reverse=True)
    if not distinct_keywords:
        st.text(resume_text)
        return
    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(word) for word in distinct_keywords) + r")(?!\w)",
        re.IGNORECASE,
    )
    highlight_background = "#31543E" if dark_mode else "#DDF4E4"
    highlight_color = "#D6F5DF" if dark_mode else "#17633A"
    highlighted = pattern.sub(
        lambda match: f'<mark style="background:{highlight_background};color:{highlight_color};border-radius:3px">'
        + html.escape(match.group(0))
        + "</mark>",
        html.escape(resume_text),
    )
    st.markdown(
        f'<div style="white-space:pre-wrap;overflow-wrap:anywhere;padding:1rem;'
        f'color:var(--cc-text);border:1px solid var(--cc-border);border-radius:8px;line-height:1.55">{highlighted}</div>',
        unsafe_allow_html=True,
    )


def render_skill_charts(result: dict, dark_mode: bool = False) -> None:
    target_skills = result["target_skills"]
    if not target_skills:
        st.info("No target skills from the built-in dictionary were found, so there is no skill-gap chart to show.")
        return
    matched_skills = set(result["matched_skills"])
    chart_text = "#ECF2F1" if dark_mode else "#1B2926"
    chart_template = "plotly_dark" if dark_mode else "plotly_white"
    gap_column, gauge_column = st.columns([1.5, 1], gap="large")
    with gap_column:
        st.markdown("#### Target skill gaps")
        figure = go.Figure(
            go.Bar(
                x=[1] * len(target_skills),
                y=target_skills,
                orientation="h",
                marker_color=["#2E8B57" if skill in matched_skills else "#C64B4B" for skill in target_skills],
                text=["Matched" if skill in matched_skills else "Gap" for skill in target_skills],
                textposition="inside",
            )
        )
        figure.update_layout(
            template=chart_template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": chart_text},
            height=max(220, 42 * len(target_skills)),
            margin=dict(l=0, r=8, t=8, b=8),
            xaxis=dict(range=[0, 1], visible=False),
            yaxis=dict(autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    with gauge_column:
        st.markdown("#### Skill match")
        match_percent = 100 * len(matched_skills) / len(target_skills)
        figure = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=match_percent,
                number={"suffix": "%", "valueformat": ".0f"},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#2E8B57"}},
            )
        )
        figure.update_layout(
            template=chart_template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": chart_text},
            height=250,
            margin=dict(l=18, r=18, t=26, b=8),
        )
        st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def append_uploaded_text(current_text: str, uploaded_files: list) -> str:
    parts = [current_text.strip()] if current_text.strip() else []
    for uploaded_file in uploaded_files:
        parts.append(extract_text(uploaded_file.name, uploaded_file.getvalue()))
    return "\n\n".join(parts)


def home_page() -> None:
    nav_brand, nav_links, nav_account = st.columns([1.1, 2.6, 1.2], vertical_alignment="center")
    with nav_brand:
        st.markdown('<div class="career-brand">ResumeHub</div>', unsafe_allow_html=True)
    with nav_links:
        st.markdown(
            '<div class="career-nav-links"><a href="#templates">Templates</a>'
            '<a href="#resources">Career notes</a><a href="#contact">Contact</a></div>',
            unsafe_allow_html=True,
        )
    with nav_account:
        with st.popover("Sign in"):
            st.markdown("#### Your ResumeHub account")
            st.info("Secure sign-in is not connected in this demo. No credentials are collected or stored.")
            st.button("Continue", disabled=True, use_container_width=True, key="login_unavailable")

    st.markdown(
        f'<section class="landing-hero" id="top" style="background-image:url(data:image/jpeg;base64,{HERO_IMAGE_BASE64})">'
        '<div class="landing-hero-content"><div class="hero-kicker">A clearer way to move forward</div>'
        '<h1>Your experience deserves a better first page.</h1>'
        '<p>Build a focused CV, see how it aligns with a role, and make your next application feel more like you.</p>'
        '<a class="hero-scroll-link" href="#build-now">Build your CV&nbsp; ↓</a></div></section>',
        unsafe_allow_html=True,
    )
    build_button, analyze_button, spacer = st.columns([1.2, 1.2, 4], gap="small")
    build_button.button("Start building", type="primary", on_click=navigate_to, args=("Build",), use_container_width=True)
    analyze_button.button("Check role fit", on_click=navigate_to, args=("Analyze",), use_container_width=True)

    feature_columns = st.columns(3)
    for column, title, description in zip(
        feature_columns,
        ("Write with purpose", "See the evidence", "Keep it readable"),
        (
            "Turn projects, study, and work into clear, truthful bullets.",
            "Understand every score and review real keyword gaps.",
            "Choose simple layouts designed to scan well on screen and on paper.",
        ),
    ):
        with column:
            st.markdown(f'<div class="feature-strip"><strong>{title}</strong><span>{description}</span></div>', unsafe_allow_html=True)

    st.markdown('<div id="templates" class="landing-section"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Layouts, not distractions</div>', unsafe_allow_html=True)
    st.header("Choose a starting point")
    st.write("Three single-column layouts with familiar headings and selectable text. Your content stays the focus.")
    template_columns = st.columns(3, gap="large")
    templates = (
        ("Classic", "Centered name, familiar hierarchy, calm blue headings.", "classic"),
        ("Modern", "Left-aligned header, teal accents, open spacing.", "modern"),
        ("Compact", "Tighter page rhythm for concise, early-career CVs.", "compact"),
    )
    for column, (template_name, description, variant) in zip(template_columns, templates):
        with column:
            st.markdown(
                f'<div class="template-paper {variant}"><div class="paper-name">YOUR NAME</div>'
                '<div class="paper-contact">City · email · portfolio</div>'
                '<div class="paper-section">PROFILE</div><div class="paper-lines"></div>'
                '<div class="paper-section">EXPERIENCE</div><div class="paper-lines"></div>'
                '<div class="paper-section">SKILLS & EDUCATION</div><div class="paper-lines"></div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"### {template_name}")
            st.caption(description)
            st.button(
                f"Use {template_name}",
                key=f"use_template_{variant}",
                on_click=navigate_to,
                args=("Build", template_name),
                use_container_width=True,
            )

    st.markdown('<div id="build-now" class="landing-section"></div>', unsafe_allow_html=True)
    process_left, process_right = st.columns([1.05, 1], gap="large", vertical_alignment="center")
    with process_left:
        st.markdown('<div class="section-kicker">From notes to next steps</div>', unsafe_allow_html=True)
        st.header("A small process. A stronger application.")
        st.markdown("**01 · Build**  Shape your experience in a clean, editable format.\n\n**02 · Compare**  Check a CV against one specific job description.\n\n**03 · Refine**  Improve a bullet without inventing evidence or numbers.")
        st.button("Open the CV builder", type="primary", on_click=navigate_to, args=("Build",), key="home_build_now")
    with process_right:
        st.image(str(ASSET_DIR / "resource-resume.jpg"), caption="Start with the evidence you already have.", use_container_width=True)

    st.markdown('<div id="resources" class="landing-section"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Career notes</div>', unsafe_allow_html=True)
    st.header("Useful reads for your next move")
    resource_columns = st.columns(3, gap="large")
    resources = (
        (
            "resource-resume.jpg",
            "Resume writing",
            "Make each bullet carry its weight",
            "Lead with what you did, add the scope or method, then include a result only when you can verify it.",
            "Try this: replace a task list with one specific action and the tool, audience, or scale involved. A truthful qualitative result is better than a guessed percentage.",
        ),
        (
            "resource-interview.jpg",
            "Interview prep",
            "Turn projects into clear stories",
            "A class project or volunteer role can show how you solve problems, work with others, and learn.",
            "Use a simple sequence: context, your responsibility, the steps you took, and what changed. Be ready to explain your own contribution separately from the team's work.",
        ),
        (
            "resource-jobsearch.jpg",
            "Job search",
            "Tailor without starting over",
            "Keep a strong base CV, then adjust the most relevant evidence for each role.",
            "Read the role requirements, identify the few skills you can genuinely support, and move that evidence higher. Never add a keyword just because it appears in the posting.",
        ),
    )
    for column, (image, category, title, summary, article) in zip(resource_columns, resources):
        with column:
            st.image(str(ASSET_DIR / image), use_container_width=True)
            st.markdown(f'<div class="resource-meta">{category}</div><div class="resource-title">{title}</div>', unsafe_allow_html=True)
            st.write(summary)
            with st.expander("Read the note"):
                st.write(article)

    st.markdown('<div id="contact" class="landing-section"></div>', unsafe_allow_html=True)
    contact_intro, contact_form = st.columns([1, 1.2], gap="large")
    with contact_intro:
        st.markdown('<div class="section-kicker">Contact</div>', unsafe_allow_html=True)
        st.header("Tell us what would help")
        st.write("Share feedback or a question about ResumeHub. This demo has no mail service connected, so submissions are not sent or retained.")
    with contact_form:
        with st.form("home_contact_form", clear_on_submit=True):
            contact_name = st.text_input("Name")
            contact_email = st.text_input("Email")
            contact_message = st.text_area("Message", height=100)
            contact_submitted = st.form_submit_button("Prepare message", use_container_width=True)
        if contact_submitted:
            if not contact_name.strip() or not contact_email.strip() or not contact_message.strip():
                st.error("Add your name, email, and message to continue.")
            else:
                st.info("Message not sent: connect a mail service before using this form for real enquiries.")
    st.markdown(
        '<div class="career-footer"><strong>ResumeHub</strong> · A practical workspace for your next application.<br>'
        '<a href="#top">Back to top ↑</a></div>',
        unsafe_allow_html=True,
    )
    footer_links = st.columns(3)
    for column, page in zip(footer_links, ("Build", "Analyze", "Theory & demo")):
        column.button(
            page,
            key=f"footer_{page.lower().replace(' ', '_').replace('&', 'and')}",
            on_click=navigate_to,
            args=(page,),
            use_container_width=True,
        )


def analyze_page() -> None:
    page_header("Resume review", "Analyze a resume", "Compare the resume with a target role. The file is read in memory and is not saved by this app.")
    guidance_panel(
        "Privacy",
        "Resume checks and rewrite suggestions run on this app server; resume text is not sent to an LLM or external API and is not intentionally saved. A hosting provider may retain operational logs, so use sample or non-sensitive documents for public demos.",
    )
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
            st.session_state.analysis_resume = resume_text
            st.session_state.analysis_error = None
            st.session_state.pop("rewrite_comparison", None)
            st.session_state.pop("rewritten_bullet_text", None)
        except Exception as exc:  # Show understandable file and input errors to the user.
            st.session_state.analysis_error = str(exc)
            st.session_state.analysis = None
            st.session_state.analysis_resume = ""

    if st.session_state.get("analysis_error"):
        st.error(st.session_state.analysis_error)

    result = st.session_state.get("analysis")
    if result:
        resume_text = st.session_state.get("analysis_resume", "")
        st.divider()
        st.subheader("Your review")
        score_col, skills_col, words_col = st.columns(3)
        score_col.metric("Guide score", f"{result['score']} / 100")
        skills_col.metric("Target skills detected", f"{len(result['matched_skills'])} / {len(result['target_skills'])}")
        words_col.metric("Resume length", f"{result['word_count']} words")
        st.caption("This is a deterministic writing checklist, not an ATS score or hiring prediction. No checker can guarantee an interview.")

        st.subheader("Score breakdown")
        for item in result["categories"]:
            label_col, bar_col, points_col = st.columns([1.5, 3, 0.6], vertical_alignment="center")
            label_col.write(f"**{item['name']}**")
            bar_col.progress(min(1.0, item["score"] / item["max"]))
            points_col.write(f"{item['score']:g}/{item['max']}")
            st.caption(item["detail"])

        st.subheader("Keywords and skills")
        matched_column, missing_column = st.columns(2, gap="large")
        with matched_column:
            matched_colors = ("#D6F5DF", "#31543E") if active_dark_mode else ("#17633A", "#DDF4E4")
            render_keyword_badges("Matched job keywords", result["matched_keywords"], *matched_colors)
            render_keyword_badges("Matched target skills", result["matched_skills"], *matched_colors)
        with missing_column:
            missing_colors = ("#FFC1C1", "#542D32") if active_dark_mode else ("#963838", "#FCE4E4")
            render_keyword_badges("Missing job keywords", result["missing_keywords"], *missing_colors)
            render_keyword_badges("Missing target skills", result["missing_skills"], *missing_colors)

        with st.expander("See matched keywords in the resume"):
            render_highlighted_resume(resume_text, result["matched_keywords"], active_dark_mode)
        render_skill_charts(result, active_dark_mode)

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

        st.subheader("Improve a bullet")
        st.caption("Choose a verb that accurately describes your contribution. Replace the placeholder only with a result you can verify; never invent numbers.")
        action_lead = "|".join(re.escape(verb) for verb in ACTION_VERBS)
        bullet_lead = re.compile(
            r"^(?:" + action_lead + r"|worked\b|helped\b|assisted\b|participated\b|responsible\s+for\b)",
            re.IGNORECASE,
        )
        bullets = [
            line.strip()
            for line in resume_text.splitlines()
            if len(line.split()) >= 4
            and (line.strip().startswith(("•", "-", "*")) or bullet_lead.match(line.strip().lstrip("•*- ")))
        ]
        if bullets:
            selected_bullet = st.selectbox(
                "Resume bullet",
                bullets,
                format_func=lambda bullet: bullet.lstrip("•*- ") if len(bullet) <= 100 else bullet.lstrip("•*- ")[:97] + "...",
            )
            selected_verb = st.selectbox(
                "Action verb",
                ["Built", "Developed", "Improved", "Implemented", "Analyzed", "Automated", "Led", "Streamlined"],
            )
            if st.button("Improve this bullet"):
                st.session_state.rewritten_bullet_text = rewrite_bullet(selected_bullet, selected_verb)
            if st.session_state.get("rewritten_bullet_text"):
                rewritten_bullet = st.text_area(
                    "Review and edit the suggested version",
                    key="rewritten_bullet_text",
                    height=100,
                )
                if st.button("Compare before and after score"):
                    updated_resume = resume_text.replace(selected_bullet, rewritten_bullet, 1)
                    try:
                        updated_result = analyze_resume(updated_resume, job_description)
                        st.session_state.rewrite_comparison = updated_result["score"]
                    except ValueError as exc:
                        st.error(str(exc))
                if st.session_state.get("rewrite_comparison") is not None:
                    before_score = result["score"]
                    after_score = st.session_state.rewrite_comparison
                    before_column, after_column = st.columns(2)
                    before_column.metric("Before", f"{before_score} / 100")
                    after_column.metric("After", f"{after_score} / 100", f"{after_score - before_score:+d} points")
                    st.caption("A higher checklist score does not mean the rewrite is more truthful or guarantees an interview. Verify every claim yourself.")
        else:
            st.info("No resume lines are long enough to treat as a bullet. Add a project or experience bullet to try the rewrite.")


def builder_page() -> None:
    page_header("Resume builder", "Build a clear, ATS-friendly resume", "Fill in only accurate information. The downloaded file uses a simple layout that is easy to edit and scan.")
    with st.form("resume_builder"):
        resume_template = st.radio("Choose a template", ["Classic", "Modern", "Compact"], key="resume_template", horizontal=True)
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
        experience_files = st.file_uploader(
            "Upload experience documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="Readable PDF, DOCX, or TXT. Extracted text is appended to Experience when you create the resume; scanned PDFs are not OCR'd.",
            key="builder_experience_files",
        )
        projects = st.text_area("Projects", height=130, placeholder="Project name | tools | dates\nBuilt ...\nAdded ...\nMeasured ... (only if measured)")
        project_files = st.file_uploader(
            "Upload project or proof documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="Readable PDF, DOCX, or TXT. Extracted text is appended to Projects when you create the resume; scanned PDFs are not OCR'd.",
            key="builder_project_files",
        )
        education = st.text_area("Education", height=90, placeholder="Degree / program, institution, location, dates. Add relevant coursework or honors only if useful.")
        certifications = st.text_area("Certifications", height=70, placeholder="Certification — Issuer — Year")
        certification_files = st.file_uploader(
            "Upload certification documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="Readable PDF, DOCX, or TXT. Extracted text is appended to Certifications when you create the resume; scanned PDFs are not OCR'd.",
            key="builder_certification_files",
        )
        submitted = st.form_submit_button("Create my resume", type="primary", use_container_width=True)

    if submitted:
        st.session_state.pop("built_resume", None)
        if not name.strip():
            st.error("Add your name before creating the resume.")
        else:
            try:
                data = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "linkedin": linkedin,
                    "summary": summary,
                    "skills": skills,
                    "experience": append_uploaded_text(experience, experience_files),
                    "projects": append_uploaded_text(projects, project_files),
                    "education": education,
                    "certifications": append_uploaded_text(certifications, certification_files),
                    "template": resume_template,
                }
            except Exception as exc:
                st.error(f"Could not read an uploaded file: {exc}")
            else:
                st.session_state.built_resume = data

    data = st.session_state.get("built_resume")
    if data:
        st.success("Your resume is ready. Open the files and check every detail before you apply.")
        col1, col2 = st.columns(2)
        col1.download_button("Download editable DOCX", build_resume_docx(data, data.get("template", "Classic")), file_name="resume.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary", use_container_width=True)
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
    st.markdown("## ✦ ResumeHub")
    st.caption("Career Studio")
    st.toggle("Dark mode", key="dark_mode", help="Switch the appearance across every page.")
    selected_page = st.radio("Navigate", ["Home", "Analyze", "Build", "Theory & demo"], key="selected_page", label_visibility="collapsed")
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
