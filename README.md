# AI Resume Analyzer — Prompt Engineering Project

**Bennett University | B.Tech 5th Semester**  
**Course:** Prompt Engineering — Applied AI Mini-Project  
**Selected Problem Statement:** **C9 — Resume feedback against a job description**  
- **Users / Source:** Students applying for placements  
- **Task:** `Resume + job description → gap list, rewritten bullet points, match score with reasons`  
- **Techniques Used:** Role prompting, rubric in prompt, structured output, prompt chaining, hallucination guardrails.

---

## 📌 Project Overview
AI Resume Analyzer is a streamlined web application built using **Streamlit** and **Google Gemini LLM** (via OpenAI-compatible endpoint). It assesses candidates' resumes against target job descriptions, providing objective match scoring, skill gap identification, and safe bullet-point rewrites without hallucinating achievements or experience.

---

## 🎯 Prompt Versions & Iteration Evidence

### 1. Version 1 (Baseline Theme) (`prompts/prompt_v1.txt`)
- **Focus:** Direct role prompting with explicit 7-point structured output:
  1. MATCH SCORE (Percentage & justification)
  2. MATCHING SKILLS (Technical & soft skills)
  3. MISSING SKILLS (Identified required gaps)
  4. STRENGTHS (Core qualifications)
  5. WEAKNESSES (Key improvement areas)
  6. IMPROVED RESUME BULLET POINTS (Rewriting existing points professionally)
  7. RECOMMENDATIONS (Actionable advice)
- **Constraint:** Use simple English, clear headings, base strictly on provided text.

### 2. Version 2 (ATS-Focused) (`prompts/prompt_v2.txt`)
- **Focus:** Tailored for student placements and ATS keyword filtering.
- **Improvements:** Stricter length constraints and concise bullet format.

### 3. Version 3 (Rubric & Scoring Rules) (`prompts/prompt_v3.txt`)
- **Focus:** Weighted scoring rubric (100 points total):
  - Technical skills match: 40 points
  - Projects & experience: 25 points
  - Education & keyword alignment: 15 points
  - Soft skills: 10 points
  - Resume clarity: 10 points
- **Improvements:** Complete breakdown of the score and refusal handling for invalid inputs.

---

## 🚀 How to Run the Project

1. **Activate the Virtual Environment**:
   ```powershell
   & "d:\prompt project\.venv\Scripts\Activate.ps1"
   ```

2. **Verify Environment Variables**:
   Ensure `GEMINI_API_KEY` is present in `d:\prompt project\.env`.

3. **Launch the Streamlit App**:
   ```powershell
   & "d:\prompt project\.venv\Scripts\streamlit.exe" run app.py
   ```

---

## 📁 Project Directory Structure
```
d:\prompt project\
│   .env                      # Gemini API credentials
│   .gitignore                # Git exclusions
│   app.py                    # Main Streamlit application
│   requirements.txt          # Dependencies list
│   README.md                 # Project documentation
├── .venv/                    # Isolated Python virtual environment
├── modules/
│   └── resume_parser.py      # PDF & DOCX text extraction module
├── prompts/
│   ├── prompt_v1.txt         # Baseline prompt (User-specified theme)
│   ├── prompt_v2.txt         # ATS student placement prompt
│   └── prompt_v3.txt         # Rubric-based evaluation prompt
├── evaluation/
│   └── experiment_log.csv    # Prompt testing and iteration log
└── test_data/                # Sample resumes and job descriptions
```
