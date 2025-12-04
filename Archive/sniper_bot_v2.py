import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🎯 SNIPER V2 CONFIGURATION
# ---------------------------------------------------------
TARGET_ROLES = ["Machine Learning Engineer", "Data Scientist", "AI Engineer"]
LOCATION = "India" 

# CHANGES: 
# 1. f_TPR=r604800 (Past WEEK instead of 24h) -> More jobs
# 2. Removed f_AL=true (Includes Non-Easy Apply jobs too, just to get data flowing)
URL_PATTERN = "https://www.linkedin.com/jobs/search/?keywords={role}&location={loc}&f_TPR=r604800&f_WT=2&sortBy=DD"

CSV_FILE = "Sniper_EasyApply_Leads.csv"
TRACKER_FILE = "Sniper_Mission_Control.html"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 SNIPER V2 (EASY APPLY MODE) ACTIVATED...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    all_jobs = []

    for role in TARGET_ROLES:
        print(f"\n🔭 Sniping Fresh Easy-Apply Jobs: {role}...")
        safe_role = urllib.parse.quote(role)
        url = URL_PATTERN.format(role=safe_role, loc=LOCATION)
        
        driver.get(url)
        time.sleep(3)
        
        # Scroll to load
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        
        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
                company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                # Get JD Text (Quick Grab)
                # Note: We will grab full JD in the AI step to save speed here
                
                if link not in [j['Apply Link'] for j in all_jobs]:
                    all_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link,
                        "Status": "Fresh"
                    })
                    print(f"   -> 🎯 Locked: {title} @ {company}")
            except:
                continue

    if all_jobs:
        df = pd.DataFrame(all_jobs)
        df.to_csv(CSV_FILE, index=False)
        print(f"\n🎉 SNIPER REPORT: {len(df)} High-Value Targets Acquired.")
        
        # Generate Tracker
        html = "<html><body><h1>🎯 Sniper Targets</h1><table>"
        for _, row in df.iterrows():
            html += f"<tr><td>{row['Job Title']}</td><td><a href='{row['Apply Link']}'>APPLY</a></td></tr>"
        html += "</table></body></html>"
        with open(TRACKER_FILE, "w", encoding="utf-8") as f: f.write(html)
    else:
        print("❌ No fresh Easy Apply jobs found. Try broadening keywords.")

if __name__ == "__main__":
    start_sniper()