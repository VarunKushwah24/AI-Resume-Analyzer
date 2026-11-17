
import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from modules.resume_parser import extract_resume_text

# Page configuration must come first
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Check your .env file.")
    st.stop()

# Gemini API client
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Load prompt template
PROMPT_PATH = Path(__file__).parent / "prompts" / "prompt_v1.txt"

with open(PROMPT_PATH, "r", encoding="utf-8") as file:
    prompt_template = file.read()

# Application interface
st.title("📄 AI Resume Analyzer")
st.subheader("Resume Feedback Against a Job Description")

st.write(
    "Upload your resume and compare it with a job description."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Upload Resume")

    resume = st.file_uploader(
        "Choose your resume",
        type=["pdf", "docx"]
    )

with col2:
    st.subheader("💼 Job Description")

    job_description = st.text_area(
        "Paste the job description",
        height=220
    )

st.divider()

# Analyze button
if st.button(
    "Analyze Resume",
    type="primary",
    use_container_width=True
):

    if resume is None:
        st.warning("Please upload your resume.")

    elif not job_description.strip():
        st.warning("Please enter a job description.")

    else:

        # Extract resume text
        with st.spinner("Reading your resume..."):
            resume_text = extract_resume_text(resume)

        if resume_text.startswith("Error reading"):
            st.error(resume_text)

        elif not resume_text:
            st.warning(
                "No readable text found. "
                "The PDF may be scanned."
            )

        else:
            st.success("Resume text extracted successfully!")

            st.subheader("Extracted Resume Content")

            st.text_area(
                "Resume Text",
                resume_text,
                height=300
            )

            st.subheader("Job Description")
            st.write(job_description)

            # AI analysis - now correctly inside else
            with st.spinner("AI is analyzing your resume..."):

                try:
                    final_prompt = prompt_template.replace(
                        "{resume_text}", resume_text
                    ).replace(
                        "{job_description}", job_description
                    )

                    response = client.chat.completions.create(
                        model="gemini-3.8-flash",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert resume analyzer."
                            },
                            {
                                "role": "user",
                                "content": final_prompt
                            }
                        ],
                        temperature=0.3
                    )

                    analysis = response.choices[0].message.content

                    st.success("Resume analysis completed!")

                    st.subheader("AI Resume Analysis")
                    st.markdown(analysis)

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

st.divider()

st.caption("AI Resume Analyzer | Milestone 2")
