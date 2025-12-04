import google.generativeai as genai
import pandas as pd
import os
from docx import Document
from docx2pdf import convert
import time

# ---------------------------------------------------------
# 🔑 SECURITY & CONFIG
# ---------------------------------------------------------
API_KEY = "AIzaSyAHkLxAcRsHC7O_DMk31kFq0njY3RVuVww" # ⚠️ REVOKE AFTER USE
INPUT_CSV = "Sniper_EasyApply_Leads.csv"
MASTER_DOCX = "Master_Resume_For_AI.docx"
OUTPUT_FOLDER = "AI_Resumes"
# ---------------------------------------------------------

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_ai_content(job_title, company):
    # The "God Mode" Prompt (#S2)
    prompt = f"""
    You are an expert Resume Writer.
    JOB: {job_title} at {company}.
    
    TASK 1: Write a 3-line Professional Summary for an ML Engineer optimizing for this job.
    TASK 2: Write 3 bullet points for a "Senior ML Engineer" role that highlight Python, AWS, and Model Deployment specific to this job title.
    
    OUTPUT FORMAT:
    SUMMARY: [Insert Summary Here]
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
    summary = ""
    experience = ""
    
    if "SUMMARY:" in text:
        parts = text.split("EXPERIENCE:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        if len(parts) > 1:
            experience = parts[1].strip()
            
    return summary, experience

def run_factory():
    print("🧠 AIM1000: GEMINI BRAIN ACTIVATED...")
    
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    df = pd.read_csv(INPUT_CSV).head(5) # Limit to 5 for testing
    
    for index, row in df.iterrows():
        company = str(row['Company']).replace(" ", "_")
        role = str(row['Job Title']).replace(" ", "_")
        print(f"\n⚙️ Analyzing: {role} @ {company}...")
        
        # 1. Ask Gemini
        ai_text = get_ai_content(row['Job Title'], row['Company'])
        if not ai_text: continue
        
        summ, exp = parse_response(ai_text)
        
        # 2. Inject into Doc
        doc = Document(MASTER_DOCX)
        for p in doc.paragraphs:
            if "{{AI_SUMMARY_INJECTION_POINT}}" in p.text:
                p.text = summ
            if "{{AI_EXPERIENCE_INJECTION_POINT}}" in p.text:
                p.text = exp
                
        # 3. Save
        filename = f"Manidhar_{company}.pdf"
        docx_path = os.path.join(OUTPUT_FOLDER, "temp.docx")
        pdf_path = os.path.join(OUTPUT_FOLDER, filename)
        
        doc.save(docx_path)
        convert(docx_path, pdf_path)
        print(f"✅ Generated: {filename}")
        time.sleep(2) # Avoid rate limits

    print(f"\n🎉 Done! Check '{OUTPUT_FOLDER}'")

if __name__ == "__main__":
    run_factory()