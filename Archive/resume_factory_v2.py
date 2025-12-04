import pandas as pd
import os
import time
from docx import Document
from docx2pdf import convert
import uuid

# ---------------------------------------------------------
# ⚙️ CONFIGURATION
# ---------------------------------------------------------
INPUT_CSV = "AIM1000_Master_List.csv"
MASTER_DOCX = "Master_Resume.docx"
OUTPUT_FOLDER = "Generated_Resumes"
DASHBOARD_FILE = "Mission_Control.html"
# ---------------------------------------------------------

# 🎯 KEYWORD STRATEGY
SKILL_MAP = {
    "data scien": "Core competencies: Statistical Analysis, A/B Testing, SQL, and Python (Pandas/NumPy).",
    "machine learning": "Relevant skills: End-to-End ML Pipelines, Docker, Kubernetes, AWS SageMaker.",
    "ml": "Relevant skills: End-to-End ML Pipelines, Docker, Kubernetes, AWS SageMaker.",
    "ai": "Technical focus: LLMs, RAG Architectures, Vector Databases, LangChain.",
    "python": "Expertise: Python Backend, FastAPI, AsyncIO, Cloud-Native Microservices.",
    "analyst": "Proficiency: SQL, Power BI, Data Visualization, Automated Reporting.",
    "default": "Strong foundation in Python, Data Engineering, and Automated Problem Solving."
}

def get_injection_text(title):
    t = str(title).lower()
    for key, text in SKILL_MAP.items():
        if key in t:
            return text
    return SKILL_MAP["default"]

def clean_filename(text):
    return "".join(c if c.isalnum() else "_" for c in str(text)).strip("_")

def generate_assets():
    print("🏭 AIM1000: RESUME FACTORY V2 STARTING...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: {INPUT_CSV} not found.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    df = pd.read_csv(INPUT_CSV)
    print(f"📊 Processing {len(df)} jobs...")

    # HTML Header
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: sans-serif; padding: 20px; background: #f4f4f9; }
            table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
            th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #0073b1; color: white; }
            tr:hover { background-color: #f1f1f1; }
            .btn { background: #0073b1; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; }
            .file-name { font-family: monospace; color: #d63384; background: #eee; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🚀 AIM1000 Mission Control</h1>
        <p>Drag the <b>Resume File</b> from your folder to the <b>Apply Link</b>.</p>
        <table>
            <tr>
                <th>Status</th>
                <th>Company</th>
                <th>Role</th>
                <th>🚀 ACTION</th>
                <th>📄 Resume to Upload</th>
            </tr>
    """

    count = 0
    for index, row in df.iterrows():
        try:
            job_title = row['Job Title']
            company = row['Company']
            link = row['Apply Link']
            
            # 1. Prepare Filename: Manidhar_{Company}_{Role}.pdf
            safe_company = clean_filename(company)[:15]
            safe_role = clean_filename(job_title)[:20]
            filename = f"Manidhar_{safe_company}_{safe_role}.pdf"
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            
            # 2. Inject & Convert (Only if PDF doesn't exist to save time)
            if not os.path.exists(output_path):
                doc = Document(MASTER_DOCX)
                injection = get_injection_text(job_title)
                
                for p in doc.paragraphs:
                    if "{{DYNAMIC_SKILL_INJECTION}}" in p.text:
                        p.text = p.text.replace("{{DYNAMIC_SKILL_INJECTION}}", injection)
                
                # Use UNIQUE temp name to avoid Permission Errors
                temp_docx = os.path.join(OUTPUT_FOLDER, f"temp_{uuid.uuid4().hex}.docx")
                doc.save(temp_docx)
                
                try:
                    convert(temp_docx, output_path)
                    print(f"✅ Generated: {filename}")
                finally:
                    if os.path.exists(temp_docx):
                        os.remove(temp_docx)
            else:
                print(f"⏭️ Skipped (Exists): {filename}")

            # 3. Add to Dashboard
            html_content += f"""
            <tr>
                <td><input type="checkbox"></td>
                <td>{company}</td>
                <td>{job_title}</td>
                <td><a href="{link}" target="_blank" class="btn">APPLY NOW ↗</a></td>
                <td><span class="file-name">{filename}</span></td>
            </tr>
            """
            count += 1

        except Exception as e:
            print(f"❌ Error on row {index}: {e}")
            continue

    # Close HTML
    html_content += "</table></body></html>"
    
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("\n" + "="*40)
    print(f"🎉 SUCCESS! {count} Resumes Generated.")
    print(f"👉 OPEN THIS FILE NOW: {DASHBOARD_FILE}")
    print("="*40)

if __name__ == "__main__":
    generate_assets()