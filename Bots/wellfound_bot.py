import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🎯 WELLFOUND CONFIG
# ---------------------------------------------------------
KEYWORDS = ["Machine Learning Engineer", "AI Engineer", "Data Scientist"]
LOCATION = "India" # or "Remote"
CSV_PATH = r"D:\AIM1000\Data\Wellfound_Leads.csv"
# ---------------------------------------------------------

def start_wellfound():
    print("🚀 Starting Wellfound Scraper...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 1. Login
    driver.get("https://wellfound.com/login")
    input("⚠️ Log in to Wellfound, then press Enter...")

    all_jobs = []

    for role in KEYWORDS:
        print(f"\n🔍 Searching: {role}...")
        # Wellfound URL structure
        url = f"https://wellfound.com/jobs?keywords={role}&location={LOCATION}"
        driver.get(url)
        time.sleep(5)
        
        # 2. Infinite Scroll (Load ~20 jobs)
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # 3. Scrape
        cards = driver.find_elements(By.CSS_SELECTOR, "[class*='JobCard_root']") # Generic class selector
        
        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "[class*='JobCard_title']").text
                company = card.find_element(By.CSS_SELECTOR, "[class*='JobCard_companyName']").text
                try:
                    # Wellfound links are often hidden, we grab the main container
                    link = driver.current_url # Simplified for now, usually requires clicking
                except:
                    link = "Apply on Wellfound"
                
                all_jobs.append({
                    "Source": "Wellfound",
                    "Job Title": title,
                    "Company": company,
                    "Apply Link": link,
                    "Status": "Pending",
                    "Date Found": time.strftime("%Y-%m-%d %H:%M")
                })
            except:
                continue

    # 4. Save
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        # Append to existing if exists
        try:
            existing = pd.read_csv(CSV_PATH)
            df = pd.concat([existing, df]).drop_duplicates(subset=['Job Title', 'Company'])
        except:
            pass
        
        df.to_csv(CSV_PATH, index=False)
        print(f"✅ Saved {len(df)} jobs to {CSV_PATH}")
    else:
        print("❌ No jobs found or selector changed.")

if __name__ == "__main__":
    start_wellfound()