import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🎯 SNIPER V5: BROADER SEARCH FOR VOLUME
# ---------------------------------------------------------
# Simplified keywords to maximize results
SEARCH_QUERY = "Python AND (AWS OR Docker OR 'Machine Learning')"

# Removed f_AL=true from URL search filter
# f_E=4 (Mid-Senior) remains for 30LPA+ targeting
URL_PATTERN = "https://www.linkedin.com/jobs/search/?keywords={keywords}&location=India&f_WT=2&f_TPR=r86400&f_E=4&sortBy=DD"

CSV_FILE = "Sniper_EasyApply_Leads.csv"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 SNIPER V5 (VOLUME MODE) ACTIVATED...")
    
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
    
    # Aggressive Scroll
    for _ in range(8):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Scrape
    cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
    
    print(f"📊 Found {len(cards)} raw cards. Filtering...")

    for card in cards:
        try:
            # We add a check here to ensure we ONLY capture Easy Apply in the saved CSV
            easy_apply = card.find_elements(By.CSS_SELECTOR, ".job-card-container__footer-item--in-easy-apply")
            if not easy_apply:
                continue # Skip if not Easy Apply
                
            title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
            company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            
            if not any(j['Apply Link'] == link for j in all_jobs):
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
        print(f"\n🎉 SNIPER REPORT: {len(df)} HIGH-MATCH JOBS SAVED.")
    else:
        print("\n❌ No jobs found that matched the final Easy Apply filter.")

if __name__ == "__main__":
    start_sniper()