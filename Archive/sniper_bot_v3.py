import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🎯 SNIPER V3: TECH STACK + HIGH VALUE TARGETING
# ---------------------------------------------------------
# #R1: Keywords based on YOUR CV, not just job titles
SEARCH_QUERY = "(Python AND (AWS OR Machine Learning OR GenAI))"

# #R2=Remote (f_WT=2)
# #R3/R5=Mid-Senior Level (f_E=4) -> Targets 30LPA+ bracket
# #R4=Easy Apply (f_AL=true)
# Time=Past 24h (r86400) to ensure volume, sorted by Date
URL_PATTERN = "https://www.linkedin.com/jobs/search/?keywords={keywords}&location=India&f_WT=2&f_TPR=r86400&f_E=4&f_AL=true&sortBy=DD"

CSV_FILE = "Sniper_EasyApply_Leads.csv"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 SNIPER V3 (HIGH VALUE TECH STACK) ACTIVATED...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    all_jobs = []

    print(f"\n🔭 Scanning Tech Stack: {SEARCH_QUERY}...")
    safe_keywords = urllib.parse.quote(SEARCH_QUERY)
    url = URL_PATTERN.format(keywords=safe_keywords)
    
    driver.get(url)
    time.sleep(3)
    
    # Aggressive Scroll to catch "Minutes ago" jobs
    for _ in range(8):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Scrape
    cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
    
    print(f"📊 Found {len(cards)} raw cards. Filtering...")

    for card in cards:
        try:
            title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
            company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            
            # #R6: Simple filter to ensure it's Engineering/Data
            title_lower = title.lower()
            if any(x in title_lower for x in ['engineer', 'developer', 'scientist', 'architect', 'lead']):
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

    # Save Results
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        df.to_csv(CSV_FILE, index=False)
        print(f"\n🎉 SNIPER REPORT: {len(df)} High-Value Targets Saved to '{CSV_FILE}'")
        print("👉 NOW RUN: python ai_tailor_v2.py")
    else:
        print("❌ No jobs found. Try removing 'f_E=4' (Mid-Senior) from URL if too strict.")

if __name__ == "__main__":
    start_sniper()