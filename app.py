import time
import os
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

# Custom styling to match user's theme screenshot
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
    .section-card {
        background-color: #1a1c23;
        border-radius: 8px;
        padding: 1.2rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📄 AI Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Resume Feedback Against a Job Description</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Upload your resume and compare it with a job description.</div>', unsafe_allow_html=True)
st.divider()

# Prompt selector in sidebar for Prompt Engineering project requirements
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
        placeholder="Paste full job description including requirements and required skills..."
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

if st.session_state.analysis:
    tab1, tab2, tab3 = st.tabs(["📊 Analysis Results", "📝 Extracted Inputs", "✨ Resume Improvement"])

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
