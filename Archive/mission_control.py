import pandas as pd
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2

# ---------------------------------------------------------
# ⚙️ CONFIG
# ---------------------------------------------------------
CV_FILENAME = "Manidhar_pati_CV 2026.pdf"
MASTER_LIST = "AIM1000_Master_List.csv"
# ---------------------------------------------------------

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text.lower()
    except:
        return ""

def get_keywords(cv_text, jd_text):
    # Simple vectorizer to find missing words
    vectorizer = CountVectorizer(stop_words='english')
    corpus = [cv_text, jd_text]
    try:
        matrix = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()
        cv_vec = matrix.toarray()[0]
        jd_vec = matrix.toarray()[1]
        
        missing = [feature_names[i] for i in range(len(feature_names)) 
                   if jd_vec[i] > 0 and cv_vec[i] == 0]
        
        # Filter for "tech-sounding" words (length > 4) to remove noise
        tech_missing = [w for w in missing if len(w) > 4][:10]
        return tech_missing
    except:
        return []

def start_mission_control():
    print("🚀 AIM1000: MISSION CONTROL STARTING...")
    
    # 1. Load Data
    if not os.path.exists(MASTER_LIST):
        print("❌ Error: Master List not found. Run the scraper first.")
        return
        
    df = pd.read_csv(MASTER_LIST)
    
    # Create 'Status' column if it doesn't exist
    if 'Status' not in df.columns:
        df['Status'] = 'Pending'
    
    # 2. Load CV
    cv_text = extract_text_from_pdf(CV_FILENAME)
    if not cv_text:
        print(f"❌ Error: Could not read {CV_FILENAME}")
        return

    # 3. Setup Browser
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 4. Login Loop
    driver.get("https://www.linkedin.com/login")
    input("⚠️ Log in to LinkedIn, then press Enter here...")

    # 5. Process Jobs
    for index, row in df.iterrows():
        if row['Status'] == 'Applied':
            continue # Skip done jobs
            
        print(f"\n" + "="*50)
        print(f"🎯 JOB #{index+1}: {row['Job Title']} @ {row['Company']}")
        print(f"🔗 Opening: {row['Apply Link']}")
        print("="*50)
        
        try:
            driver.get(row['Apply Link'])
            time.sleep(3) # Wait for load
            
            # --- INTELLIGENCE LAYER ---
            # Try to grab the JD text automatically
            try:
                # Click "See more" if it exists to get full text
                try:
                    driver.find_element(By.CLASS_NAME, "jobs-description__footer-button").click()
                except:
                    pass
                
                jd_text = driver.find_element(By.ID, "job-details").text.lower()
                missing_words = get_keywords(cv_text, jd_text)
                
                print("\n🧠 AUTOMATED ANALYSIS:")
                print(f"⚠️ MISSING KEYWORDS: {', '.join(missing_words)}")
                print("-" * 30)
                print("📝 SUGGESTED 'ABOUT' SECTION (Copy-Paste this):")
                print(f"\"Applied ML Engineer with exp in {', '.join(missing_words[:3])}. Proven track record in FastAPI, Docker, and Predictive Analytics.\"")
                print("-" * 30)
                
            except:
                print("⚠️ Could not auto-read JD (Layout differs).")

            # --- ACTION LAYER ---
            choice = input("👉 Did you apply? (y = Yes / s = Skip / q = Quit): ").lower()
            
            if choice == 'y':
                df.at[index, 'Status'] = 'Applied'
                df.to_csv(MASTER_LIST, index=False) # Save immediately
                print("✅ Marked as Applied.")
            elif choice == 'q':
                break
            else:
                print("⏭️ Skipped.")
                
        except Exception as e:
            print(f"❌ Error opening link: {e}")
            
    print("👋 Mission Control Closed.")

if __name__ == "__main__":
    start_mission_control()