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
INPUT_CSV = "Sniper_Hourly_Leads.csv"
OUTPUT_FOLDER = "Generated_Resumes"
MASTER_DOCX = "Master_Resume.docx"
# ---------------------------------------------------------

genai.configure(api_key=AIzaSyAHkLxAcRsHC7O_DMk31kFq0njY3RVuVww)
model = genai.GenerativeModel('models/gemini-2.5-flash')

def get_tailored_content(job_title, company):
    # This prompt fixes the "Double Summary" issue by generating replacement text only
    prompt = f"""
    Act as an expert Resume Writer for a Senior ML/IoT Engineer.
    Target Job: {job_title} at {company}.
    
    TASK 1 (Summary): Write a SINGLE 3-line professional summary. Start with "Applied Machine Learning Engineer...". Focus on Python, AWS, and skills relevant to this job.
    
    TASK 2 (Project): Invent a project title and description that applies the candidate's core skills (IoT, Real-time Data, ML, Semiconductor) to the requirements of {job_title}.
    Format: "Project: [Title] | GitHub: github.com/Manidhar8008/[repo] \n - [Bullet 1] \n - [Bullet 2]"
    
    OUTPUT FORMAT:
    SUMMARY_TEXT: [Insert Summary Here]
    PROJECT_TEXT: [Insert Project Here]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return None

def run_factory():
    print("🧠 AI FACTORY STARTED...")
    
    if not os.path.exists(INPUT_CSV):
        print("❌ Error: Run Sniper first!")
        return
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

    df = pd.read_csv(INPUT_CSV)
    
    for index, row in df.iterrows():
        clean_company = "".join(c for c in str(row['Company']) if c.isalnum())[:15]
        clean_role = "".join(c for c in str(row['Job Title']) if c.isalnum())[:20]
        filename = f"Manidhar_{clean_company}_{clean_role}.pdf"
        pdf_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if os.path.exists(pdf_path): continue 
        
        print(f"⚙️ Tailoring for: {row['Company']}...")
        ai_response = get_tailored_content(row['Job Title'], row['Company'])
        
        if ai_response:
            try:
                doc = Document(MASTER_DOCX)
                
                # Parse AI response
                summ = ""
                proj = ""
                if "SUMMARY_TEXT:" in ai_response:
                    parts = ai_response.split("PROJECT_TEXT:")
                    summ = parts[0].replace("SUMMARY_TEXT:", "").strip()
                    if len(parts) > 1: proj = parts[1].strip()

                # Inject into Doc
                for p in doc.paragraphs:
                    if "{{DYNAMIC_SUMMARY_INJECTION}}" in p.text:
                        p.text = summ
                    if "{{DYNAMIC_PROJECT_INJECTION}}" in p.text:
                        p.text = proj
                
                temp_docx = os.path.join(OUTPUT_FOLDER, "temp.docx")
                doc.save(temp_docx)
                convert(temp_docx, pdf_path)
                if os.path.exists(temp_docx): os.remove(temp_docx)
                
                print(f"   ✅ Created: {filename}")
                time.sleep(2)
            except Exception as e:
                print(f"   ⚠️ Error: {e}")

    print(f"\n🎉 BATCH COMPLETE. Check '{OUTPUT_FOLDER}'")

if __name__ == "__main__":
    run_factory()