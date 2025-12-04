import pandas as pd
import os
import time
from docx import Document
from docx2pdf import convert
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# ⚙️ CONFIG
# ---------------------------------------------------------
MASTER_DOCX = "Master_Resume.docx"
MASTER_LIST = "AIM1000_Master_List.csv"
OUTPUT_FOLDER = "Ready_To_Apply"
# ---------------------------------------------------------

# Create output folder if not exists
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_benefit_score(jd_text):
    # Keywords for "Fast Growth" and "Benefits"
    growth_keywords = ["startup", "growth", "scale", "equity", "stock options", "ownership", "fast-paced", "series b", "series c"]
    benefit_keywords = ["health", "insurance", "bonus", "unlimited pto", "remote", "flexible", "401k", "learning budget"]
    
    score = 0
    found_perks = []
    
    for word in growth_keywords + benefit_keywords:
        if word in jd_text:
            score += 1
            found_perks.append(word)
            
    return score, list(set(found_perks))

def inject_keywords_and_convert(job_title, company, missing_keywords):
    try:
        doc = Document(MASTER_DOCX)
        
        # 1. Craft the Injection Sentence
        if missing_keywords:
            top_3 = ", ".join(missing_keywords[:3]).title() # Capitalize them
            injection = f"Key technical competencies relevant to this role include {top_3}, ensuring immediate contribution to the engineering team."
        else:
            injection = "I am fully prepared to leverage my technical stack to drive immediate value for this role."

        # 2. Find and Replace Placeholder
        replaced = False
        for paragraph in doc.paragraphs:
            if "{{TARGETED_COMPETENCY_SENTENCE}}" in paragraph.text:
                paragraph.text = paragraph.text.replace("{{TARGETED_COMPETENCY_SENTENCE}}", injection)
                replaced = True
                break
        
        if not replaced:
            print("⚠️ Warning: Placeholder {{TARGETED_COMPETENCY_SENTENCE}} not found in DOCX.")

        # 3. Save Temporary Docx
        clean_company = "".join(x for x in company if x.isalnum())
        temp_docx = os.path.join(OUTPUT_FOLDER, f"Resume_{clean_company}.docx")
        final_pdf = os.path.join(OUTPUT_FOLDER, f"Manidhar_Pati_{clean_company}.pdf")
        
        doc.save(temp_docx)
        
        # 4. Convert to PDF (Uses local Word)
        convert(temp_docx, final_pdf)
        
        # Cleanup temp file
        os.remove(temp_docx)
        
        return final_pdf
    except Exception as e:
        print(f"❌ Error creating resume: {e}")
        return None

def start_factory():
    print("🏭 AIM1000: RESUME FACTORY STARTING...")
    
    df = pd.read_csv(MASTER_LIST)
    if 'Status' not in df.columns: df['Status'] = 'Pending'

    # Setup Browser
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get("https://www.linkedin.com/login")
    input("⚠️ Log in to LinkedIn, then press Enter...")

    for index, row in df.iterrows():
        if row['Status'] == 'Applied': continue

        print(f"\n🏭 Processing: {row['Job Title']} @ {row['Company']}")
        
        try:
            driver.get(row['Apply Link'])
            time.sleep(3)
            
            # 1. GET JD
            try:
                try: driver.find_element(By.CLASS_NAME, "jobs-description__footer-button").click()
                except: pass
                jd_text = driver.find_element(By.ID, "job-details").text.lower()
            except:
                print("⚠️ Could not read JD. Skipping analysis.")
                continue

            # 2. ANALYZE (Fit + Benefits)
            # (Re-using vectorizer logic strictly for keywords)
            vectorizer = CountVectorizer(stop_words='english')
            # Fake CV text just to find gaps (You would load your real text here)
            cv_dummy = "python machine learning sql data analysis" 
            matrix = vectorizer.fit_transform([cv_dummy, jd_text])
            feature_names = vectorizer.get_feature_names_out()
            jd_vec = matrix.toarray()[1]
            missing = [feature_names[i] for i in range(len(feature_names)) if jd_vec[i] > 0][:5]
            
            # Benefit Analysis
            ben_score, perks = get_benefit_score(jd_text)
            
            print("-" * 40)
            print(f"💎 BENEFIT SCORE: {ben_score}/10")
            print(f"💰 Perks Found: {', '.join(perks)}")
            print(f"🔧 Missing Skills to Inject: {', '.join(missing)}")
            print("-" * 40)
            
            if ben_score < 2:
                print("❌ Low Benefits/Growth Signals. Skipping...")
                continue

            # 3. CREATE RESUME
            print("⚙️ Generating Custom Resume...")
            pdf_path = inject_keywords_and_convert(row['Job Title'], row['Company'], missing)
            
            if pdf_path:
                print(f"✅ READY: {pdf_path}")
                print("👉 ACTION: Click 'Apply' on Chrome and upload this specific PDF.")
                
                choice = input("Did you apply? (y/n): ")
                if choice.lower() == 'y':
                    df.at[index, 'Status'] = 'Applied'
                    df.to_csv(MASTER_LIST, index=False)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    start_factory()