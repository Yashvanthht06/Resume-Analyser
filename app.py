import streamlit as st
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import re
import pandas as pd
import time
from rapidfuzz import process

st.set_page_config(page_title="Resume Analyzer", layout="wide")

st.markdown("""
<style>

/* -------- HEADER STYLE -------- */
.main-header {
    background-color:#1E2E4F;
    padding:22px;
    text-align:center;
    border-radius:12px;
    margin-bottom:25px;
    box-shadow:0px 4px 10px rgba(0,0,0,0.25);
}
.main-header h1 {
    color:white;
    margin:0;
    font-size:38px;
    letter-spacing:1px;
    font-weight:600;
}

/* -------- SELECTBOX STYLE -------- */
div[data-baseweb="select"] > div {
    background-color: white !important;
    border-radius: 12px !important;
    min-height: 65px !important;
    padding: 12px 16px !important;
    border: 2px solid #31487A !important;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.08);
}

div[data-baseweb="select"] span {
    color: black !important;
    font-size: 20px !important;
    font-weight: 500 !important;
}

div[data-baseweb="select"] svg {
    fill: #31487A !important;
}

div[data-baseweb="select"] > div:hover {
    border-color: #1E2E4F !important;
}

ul[role="listbox"] li {
    font-size: 18px !important;
    padding: 10px !important;
}

/* -------- TEXT AREA -------- */
textarea {
    border-radius:10px !important;
    font-size:15px !important;
}

/* -------- FILE UPLOADER -------- */
section[data-testid="stFileUploader"] {
    border-radius:12px;
    padding:10px;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="main-header">
    <h1>Resume Analyzer</h1>
</div>
""", unsafe_allow_html=True)





def clean_text(text):
    text = text.lower()
    replacements = {
        "machine learning": "machine_learning",
        "data analysis": "data_analysis",
        "deep learning": "deep_learning",
        "power bi": "power_bi",
        "ci cd": "ci_cd"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    text = re.sub(r'[^a-z0-9_ ]', ' ', text)
    return text


def fuzzy_match(skill, skills_db, threshold=85):
    try:
        match = process.extractOne(skill, skills_db)
        if match and match[1] >= threshold:
            return match[0]
    except:
        return None
    return None


def calculate_weighted_score(user_skills, role_skills):
    matched = len(set(user_skills) & set(role_skills))
    return matched / len(role_skills) if role_skills else 0

def calculate_resume_score(ratio):
    return int(ratio * 100)

skills_db = ["python","java","sql","machine_learning","deep_learning",
"data_analysis","aws","docker","kubernetes","html","css","react","nodejs"]

roles_df = pd.read_csv("job_roles.csv")

def extract_skills_from_text(text, skills_db):
    tokens = text.split()
    detected = set()

    for token in tokens:
        if token in skills_db:
            detected.add(token)
        else:
            fuzzy = fuzzy_match(token, skills_db)
            if fuzzy:
                detected.add(fuzzy)

    return list(detected)

uploaded_file = st.file_uploader("Upload Resume (PDF)")

if uploaded_file:

    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    raw_text = extract_text("temp.pdf", laparams=LAParams())
    cleaned_text = clean_text(raw_text)

    found_skills = extract_skills_from_text(cleaned_text, skills_db)


    ranked_roles = []
    for _, row in roles_df.iterrows():
        role = row["role"]
        role_skills = row["skills"].split("|")
        score = calculate_weighted_score(found_skills, role_skills)
        ranked_roles.append((role, score))

    ranked_roles.sort(key=lambda x: x[1], reverse=True)
    ranked_roles = ranked_roles[:5]

    st.markdown("""
    <div style="background:#31487A;padding:15px;border-radius:10px;">
    <h3 style="color:white;text-align:center;margin:0;">Top Career Matches</h3>
    </div>
    """, unsafe_allow_html=True)

    for role, score in ranked_roles:
        st.markdown(f"""
        <div style="background:#8FB3E2;padding:12px;margin-top:8px;border-radius:8px;">
        <b>{role}</b> → {round(score*100,2)}% match
        </div>
        """, unsafe_allow_html=True)


    st.markdown("""
    <div style="background:#31487A;padding:12px;border-radius:10px;margin-top:25px;">
    <h4 style="color:white;margin:0;">Select Role to Analyze Skill Gap</h4>
    </div>
    """, unsafe_allow_html=True)

    selected_role = st.selectbox("", roles_df["role"].tolist())

    role_skills = roles_df[roles_df["role"] == selected_role]["skills"].values[0].split("|")

    
    st.markdown("""
    <div style="background:#31487A;padding:12px;border-radius:10px;margin-top:20px;">
    <h4 style="color:white;margin:0;">Required Skills</h4>
    </div>
    """, unsafe_allow_html=True)

    required_text = "\n".join([f"{i+1}. {s}" for i,s in enumerate(role_skills)])
    st.text_area("", required_text, height=200)


    missing_skills = list(set(role_skills) - set(found_skills))

    st.markdown("""
    <div style="background:#192338;padding:12px;border-radius:10px;margin-top:20px;">
    <h4 style="color:#FF6B6B;margin:0;">⚠ Missing Skills (Need to Learn)</h4>
    </div>
    """, unsafe_allow_html=True)

    if missing_skills:
        missing_text = "\n".join([f"{i+1}. {s}" for i,s in enumerate(missing_skills)])
        st.text_area("", missing_text, height=200)
    else:
        st.success("You match all required skills!")


    ratio = calculate_weighted_score(found_skills, role_skills)
    score = calculate_resume_score(ratio)

    st.subheader("Resume Score")

    col1, col2, col3 = st.columns([1,2,5])

    with col1:
        st.markdown("<p style='font-size:20px;margin-top:18px;'><b>Score</b></p>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"<p style='font-size:42px;color:#1E2E4F;font-weight:600;'>{score}/100</p>", unsafe_allow_html=True)

    with col3:
        progress = st.progress(0)
        for i in range(score + 1):
            progress.progress(i / 100)
            time.sleep(0.01)
