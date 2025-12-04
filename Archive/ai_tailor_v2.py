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
INPUT_CSV = "Sniper_EasyApply_Leads.csv"
MASTER_DOCX = "Master_Resume_For_AI.docx"
OUTPUT_FOLDER = "AI_Resumes"
# ---------------------------------------------------------

genai.configure(api_key=API_KEY)
# UPDATED MODEL NAME TO FIX 404 ERROR
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_content(job_title, company):
    prompt = f"""
    You are an expert Resume Writer for a Senior ML Engineer (3-5 YOE).
    Target Job: {job_title} at {company}.
    
    TASK 1: Write a professional summary emphasizing Python, AWS, and Scalable ML Systems.
    TASK 2: Write 3 bullet points for a "Senior ML Engineer" role achievement section.
    
    OUTPUT FORMAT:
    SUMMARY: [Text]
    EXPERIENCE:
    * [Text]
    * [Text]
    * [Text]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None

def parse_response(text):
    summary = "Experienced ML Engineer specializing in scalable IoT and Cloud architectures."
    experience = "* Built end-to-end ML pipelines processing 500k+ daily events.\n* Optimized inference latency by 40% using Docker and AWS SageMaker.\n* Deployed predictive maintenance models reducing downtime by 25%."
    
    if text and "SUMMARY:" in text:
        parts = text.split("EXPERIENCE:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        if len(parts) > 1:
            experience = parts[1].strip()
            
    return summary, experience

def run_factory():
    print("🧠 AIM1000: BRAIN V2 (FLASH) ACTIVATED...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: {INPUT_CSV} not found. Run the Sniper first (or create test data).")
        return

    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    
    df = pd.read_csv(INPUT_CSV)
    print(f"📊 Processing {len(df)} jobs...")
    
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