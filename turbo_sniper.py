import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🚀 TURBO SNIPER CONFIGURATION
# ---------------------------------------------------------
# KEYWORDS: Broad but relevant. We filter garbage later.
SEARCH_QUERY = "(Python AND (AWS OR Docker OR MLOps OR GenAI))"
LOCATION = "India" 

# URL: Past 24h (r86400), Remote (f_WT=2), Sorted by Date (DD)
URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}&f_TPR=r86400&f_WT=2&sortBy=DD"
CSV_FILE = "output/Turbo_Leads.csv"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 TURBO SNIPER STARTED (FAST MODE)...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.page_load_strategy = 'eager' # Don't wait for images
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    print(f"\n🔭 Scanning: {SEARCH_QUERY}...")
    safe_query = urllib.parse.quote(SEARCH_QUERY)
    url = URL_TEMPLATE.format(query=safe_query, loc=LOCATION)
    
    driver.get(url)
    time.sleep(3)

    # FAST SCROLL (Load 200+ jobs)
    print("📜 Scrolling for 60 seconds to load 200+ jobs...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(20): 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                # Try clicking "See more jobs" button if it exists
                driver.find_element(By.XPATH, "//button[contains(@class, 'jobs-search__left-rail__content__button')]").click()
                time.sleep(2)
            except:
                break
        last_height = new_height
        print(f"   -> Scroll {i+1}/20...")

    # GRAB EVERYTHING
    cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
    print(f"📊 Found {len(cards)} raw cards. Extracting...")

    all_jobs = []
    for card in cards:
        try:
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
        except:
            continue

    # FORCE SAVE
    df = pd.DataFrame(all_jobs)
    # Filter for keywords in Title to ensure quality (Python filter)
    df = df[df['Job Title'].str.contains('Engineer|Developer|Scientist|Architect|Lead', case=False, na=False)]
    
    df.to_csv(CSV_FILE, index=False)
    print("\n" + "="*50)
    print(f"🎉 DONE: {len(df)} High-Quality Leads Saved to '{CSV_FILE}'")
    print("="*50)

if __name__ == "__main__":
    start_sniper()