import time
import os
import re
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from modules.resume_parser import extract_resume_text

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("Gemini API key not found. Add GEMINI_API_KEY to your .env file or Streamlit secrets.")
    st.stop()

# Initialize OpenAI-compatible client for Gemini
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=40.0,
    max_retries=0,
)

# Active models with available quota, primary and fallback
MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.5-flash"]
RETRYABLE_CODES = ("503", "429", "500", "502", "504", "timed out", "Timeout", "APITimeoutError")


def call_llm(system_msg, user_msg, temperature=0.3, retries=2, status=None):
    """Call Gemini with retry (exponential backoff) and model fallback."""
    def log(text):
        if status is not None:
            status.write(text)

    last_error = None
    for model in MODELS:
        for attempt in range(retries):
            start = time.time()
            try:
                log(f"Trying `{model}` (attempt {attempt + 1}/{retries})...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=temperature,
                )
                log(f"✅ `{model}` responded in {time.time() - start:.1f}s")
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                log(f"❌ `{model}` failed after {time.time() - start:.1f}s: {str(e)[:150]}")
                if any(code in str(e) for code in RETRYABLE_CODES):
                    time.sleep(2 ** attempt)
                    continue
                break
    raise last_error


# Prompt selection helper
PROMPTS_DIR = Path(__file__).parent / "prompts"
available_prompts = {
    "Prompt V1 (Baseline Theme)": PROMPTS_DIR / "prompt_v1.txt",
    "Prompt V2 (ATS Focused)": PROMPTS_DIR / "prompt_v2.txt",
    "Prompt V3 (Rubric & Scoring Rules)": PROMPTS_DIR / "prompt_v3.txt",
}

# Preserve state across Streamlit reruns
for key in ("resume_text", "job_description", "analysis", "improvement"):
    if key not in st.session_state:
        st.session_state[key] = None

# Custom styling for a polished look matching the dark theme
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    .tagline {
        color: #a0aec0;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1f2430 0%, #161922 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1.2rem;
    }
    .badge-matched {
        display: inline-block;
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.35);
        border-radius: 9999px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 0.88rem;
        font-weight: 500;
    }
    .badge-missing {
        display: inline-block;
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-radius: 9999px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 0.88rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📄 AI Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Resume Feedback Against a Job Description</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Upload your resume and compare it with a job description.</div>', unsafe_allow_html=True)
st.divider()

# Prompt selector in sidebar
with st.sidebar:
    st.header("⚙️ Prompt Engineering Controls")
    selected_prompt_name = st.selectbox(
        "Select Prompt Version",
        list(available_prompts.keys()),
        index=0
    )
    prompt_file = available_prompts[selected_prompt_name]
    if prompt_file.exists():
        with open(prompt_file, "r", encoding="utf-8") as f:
            active_prompt_template = f.read()
    else:
        st.error(f"Prompt file not found: {prompt_file}")
        active_prompt_template = ""

    with st.expander("View Active Prompt Template"):
        st.code(active_prompt_template, language="text")

    st.markdown("---")
    st.caption("Bennett University B.Tech 5th Sem | Prompt Engineering Project C9")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📁 Upload Resume")
    resume = st.file_uploader("Choose your resume", type=["pdf", "docx"])
    
with col2:
    st.subheader("💼 Job Description")
    job_description = st.text_area(
        "Paste the job description",
        height=220,
        placeholder="Paste full job description including requirements and skills..."
    )

st.divider()

if st.button("Analyze Resume", type="primary", use_container_width=True):
    if resume is None:
        st.warning("Please upload your resume (PDF or DOCX).")
    elif not job_description.strip():
        st.warning("Please enter a job description.")
    else:
        with st.spinner("Reading resume contents..."):
            resume_text = extract_resume_text(resume)

        if isinstance(resume_text, str) and resume_text.startswith("Error reading"):
            st.error(resume_text)
        elif not resume_text or not resume_text.strip():
            st.warning("No readable text found in resume. If it is a scanned PDF, please use a text-based PDF or DOCX.")
        else:
            final_prompt = active_prompt_template.replace(
                "{resume_text}", resume_text
            ).replace(
                "{job_description}", job_description
            )
            try:
                with st.status("AI is analyzing your resume...", expanded=True) as status:
                    analysis = call_llm(
                        "You are an expert AI Resume Analyzer.",
                        final_prompt,
                        temperature=0.3,
                        status=status,
                    )
                    status.update(label="Analysis completed successfully!", state="complete", expanded=False)
                st.session_state.resume_text = resume_text
                st.session_state.job_description = job_description
                st.session_state.analysis = analysis
                st.session_state.improvement = None
                st.success("Resume analysis completed!")
            except Exception as e:
                st.error("The AI service is temporarily busy. Please retry in a few moments.")
                st.caption(f"Details: {e}")


def parse_score_and_skills(analysis_text):
    """Extract score and skills for interactive UI widgets."""
    score = None
    score_match = re.search(r'(?:Match Score|Score)[:\s*]+(\d{1,3})%', analysis_text, re.IGNORECASE)
    if score_match:
        try:
            score = int(score_match.group(1))
            score = max(0, min(100, score))
        except ValueError:
            score = None

    matched_skills = []
    missing_skills = []

    m_section = re.search(r'(?:###?\s*2\.\s*MATCHING SKILLS|MATCHING SKILLS)(.*?)(?:###?\s*3\.\s*MISSING SKILLS|MISSING SKILLS|$)', analysis_text, re.DOTALL | re.IGNORECASE)
    if m_section:
        lines = m_section.group(1).split('\n')
        for line in lines:
            line = re.sub(r'^[\*\-\d\.]+\s*', '', line).strip()
            # Clean bold text or colons
            item = line.split(':')[0].replace('*', '').strip()
            if item and len(item) < 40 and not item.lower().startswith(('matching', 'skills', 'technical', 'none')):
                matched_skills.append(item)

    miss_section = re.search(r'(?:###?\s*3\.\s*MISSING SKILLS|MISSING SKILLS)(.*?)(?:###?\s*4\.\s*STRENGTHS|STRENGTHS|$)', analysis_text, re.DOTALL | re.IGNORECASE)
    if miss_section:
        lines = miss_section.group(1).split('\n')
        for line in lines:
            line = re.sub(r'^[\*\-\d\.]+\s*', '', line).strip()
            item = line.split(':')[0].replace('*', '').strip()
            if item and len(item) < 40 and not item.lower().startswith(('missing', 'skills', 'technical', 'none')):
                missing_skills.append(item)

    return score, matched_skills[:10], missing_skills[:10]


if st.session_state.analysis:
    score, matched_skills, missing_skills = parse_score_and_skills(st.session_state.analysis)

    # FEATURE 1: Interactive Score Card & Visual Skill Pills
    st.markdown("### 🎯 Executive Dashboard Overview")
    metric_col1, metric_col2 = st.columns([1, 2])

    with metric_col1:
        if score is not None:
            if score >= 75:
                score_color = "🟢 Strong Candidate"
            elif score >= 50:
                score_color = "🟡 Moderate Match"
            else:
                score_color = "🔴 Needs Improvement"

            st.metric(label="Resume Match Score", value=f"{score}%", delta=score_color)
            st.progress(score / 100.0)
        else:
            st.info("Match score detailed in analysis below.")

    with metric_col2:
        if matched_skills or missing_skills:
            if matched_skills:
                st.markdown("**Matched Skills Found:**")
                badges_matched_html = "".join([f'<span class="badge-matched">✓ {skill}</span>' for skill in matched_skills])
                st.markdown(badges_matched_html, unsafe_allow_html=True)

            if missing_skills:
                st.markdown("**Important Missing Skills:**")
                badges_missing_html = "".join([f'<span class="badge-missing">✕ {skill}</span>' for skill in missing_skills])
                st.markdown(badges_missing_html, unsafe_allow_html=True)
        else:
            st.markdown("*Skills breakdown available in the detailed analysis.*")

    st.markdown("<br>", unsafe_allow_html=True)

    # FEATURE 2: One-Click Export Report Button
    full_report_text = f"""==================================================
AI RESUME ANALYZER - EVALUATION REPORT
Bennett University Prompt Engineering (Project C9)
==================================================

Target Job Description:
-----------------------
{st.session_state.job_description}

Candidate Resume Text:
----------------------
{st.session_state.resume_text}

Detailed AI Analysis:
---------------------
{st.session_state.analysis}

==================================================
AI Resume Improvements (if generated):
--------------------------------------------------
{st.session_state.improvement or 'Not generated yet.'}
==================================================
"""
    st.download_button(
        label="📥 Download Full Evaluation Report (.txt)",
        data=full_report_text,
        file_name="Resume_Analysis_Report.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 Detailed Analysis", "📝 Extracted Inputs", "✨ Resume Improvement"])

    with tab1:
        st.markdown("### AI Resume Analysis")
        st.markdown(st.session_state.analysis)

    with tab2:
        col_res, col_jd = st.columns(2)
        with col_res:
            st.markdown("#### Extracted Resume Text")
            st.text_area("Extracted Resume", st.session_state.resume_text, height=300, disabled=True)
        with col_jd:
            st.markdown("#### Provided Job Description")
            st.text_area("Job Description", st.session_state.job_description, height=300, disabled=True)

    with tab3:
        st.markdown("### ✨ AI Resume Improvement Assistant")
        st.write(
            "Get improved resume wording strictly based on your actual resume. "
            "The AI is constrained to not invent skills, experience, or achievements."
        )

        if st.button("Generate Bullet Point & Summary Improvements", use_container_width=True):
            improvement_prompt = f"""
You are a careful professional resume editor.
Use only facts explicitly supported by the candidate's resume.
Do not invent skills, tools, work experience, education, certifications,
numbers, achievements, or responsibilities.

Target job description:
{st.session_state.job_description}

Resume text:
{st.session_state.resume_text}

Previous resume analysis:
{st.session_state.analysis}

Create these sections:
1. Improved Professional Summary: rewrite only if enough information exists.
2. Improved Resume Bullet Points: rewrite up to 5 existing points, keeping their meaning.
3. Relevant Skills to Highlight: list only skills already in the resume.
4. Missing Information: list useful details the candidate may add only if true.
5. Final Safety Check: confirm no unsupported experience or skills were added.
"""
            try:
                with st.status("Creating resume improvement suggestions...", expanded=True) as status:
                    improvement = call_llm(
                        "You improve resumes without fabricating candidate information.",
                        improvement_prompt,
                        temperature=0.2,
                        status=status,
                    )
                    status.update(label="Suggestions ready!", state="complete", expanded=False)
                st.session_state.improvement = improvement
                st.success("Resume improvements generated!")
            except Exception as e:
                st.error("The AI service is busy. Please try again in a minute.")
                st.caption(f"Details: {e}")

        if st.session_state.improvement:
            st.markdown("---")
            st.markdown(st.session_state.improvement)

st.divider()
st.caption("AI Resume Analyzer | Bennett University Prompt Engineering Applied AI Project (Problem C9)")
