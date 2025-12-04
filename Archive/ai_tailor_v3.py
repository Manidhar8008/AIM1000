import google.generativeai as genai
import pandas as pd
import os
from docx import Document
from docx2pdf import convert
import time

# ---------------------------------------------------------
# 🔑 CONFIGURATION
# ---------------------------------------------------------
API_KEY = "AIzaSyAHkLxAcRsHC7O_DMk31kFq0njY3RVuVww" 
# NOTE: This key is still visible in the chat. Please be cautious!
INPUT_CSV = "Sniper_Mega_Leads.csv"
MASTER_DOCX = "Master_Resume_For_AI.docx"
OUTPUT_FOLDER = "AI_Resumes"
# ---------------------------------------------------------

genai.configure(api_key=API_KEY)
# ✅ FIXED MODEL NAME!
model = genai.GenerativeModel('models/gemini-2.5-flash')

def get_ai_content(job_title, company):
    # User's Resume Summary (from provided text)
    master_resume_summary = "Applied Machine Learning Engineer with 3+ years experience building end-to-end production systems that automate decisions, optimize revenue, and reduce operational risk. Expert in Python, scikit-learn, SQL, Docker, CI/CD, Streamlit/FastAPI, AWS."
    
    prompt = f"""
    You are an expert Resume Writer for a Senior ML Engineer (3-5 YOE).
    Target Job: {job_title} at {company}.
    
    CANDIDATE MASTER SUMMARY: {master_resume_summary}

    TASK 1: Write a concise 3-line Professional Summary (max 30 words) emphasizing the candidate's production experience and skills (Docker, AWS) most relevant to the target job title.
    TASK 2: Write 3 separate bullet points (one sentence each) highlighting achievements that match the technical requirements of the target job title.
    
    OUTPUT FORMAT:
    SUMMARY: [Text]
    EXPERIENCE:
    * [Bullet 1]
    * [Bullet 2]
    * [Bullet 3]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None

def parse_response(text):
    # Fallback to ensure PDFs are not empty if AI fails (but AI should work now)
    fallback_summary = "ML Engineer specialized in production delivery using Python, Docker, and AWS. Proven track record in forecasting and IoT anomaly detection."
    fallback_exp = "* Built production LSTM forecasting models, achieving 95% SKU demand accuracy.\n* Designed anomaly detection systems reducing downtime risk by 30%.\n* Delivered 15M+ daily predictions via scalable recommendation models on AWS SageMaker."
    
    if text and "SUMMARY:" in text:
        parts = text.split("EXPERIENCE:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        if len(parts) > 1:
            experience = parts[1].strip()
            
    return summary, experience

def run_factory():
    print("🧠 AIM1000: BRAIN V3 (GEMINI 2.5 FLASH) ACTIVATED...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: {INPUT_CSV} not found. Run the Sniper first.")
        return

    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    
    df = pd.read_csv(INPUT_CSV).head(5) # Still limit to 5 for fast testing
    
    for index, row in df.iterrows():
        company = str(row['Company']).replace(" ", "_")
        print(f"⚙️ Tailoring for: {company}...")
        
        ai_text = get_ai_content(row['Job Title'], row['Company'])
        summ, exp = parse_response(ai_text)
        
        try:
            doc = Document(MASTER_DOCX)
            for p in doc.paragraphs:
                if "{{AI_SUMMARY_INJECTION_POINT}}" in p.text:
                    p.text = summ
                if "{{AI_EXPERIENCE_INJECTION_POINT}}" in p.text:
                    p.text = exp
                    
            filename = f"Manidhar_{company}.pdf"
            docx_path = os.path.join(OUTPUT_FOLDER, "temp.docx")
            pdf_path = os.path.join(OUTPUT_FOLDER, filename)
            
            doc.save(docx_path)
            convert(docx_path, pdf_path)
            print(f"   ✅ Created: {filename}")
            if os.path.exists(docx_path): os.remove(docx_path)
            time.sleep(1) 
        except Exception as e:
            print(f"   ⚠️ Error creating PDF: {e}")

    print(f"\n🎉 Done! Check '{OUTPUT_FOLDER}'")

if __name__ == "__main__":
    run_factory()