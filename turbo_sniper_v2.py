import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🚀 TURBO SNIPER V2 CONFIGURATION
# ---------------------------------------------------------
SEARCH_QUERY = "(Python AND (AWS OR Docker OR MLOps OR GenAI))"
LOCATION = "India" 
URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}&f_TPR=r86400&f_WT=2&sortBy=DD"
CSV_FILE = "output/Turbo_Leads.csv"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 TURBO SNIPER V2 ACTIVATED...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.page_load_strategy = 'normal' # Switched back to normal for stability
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    print(f"\n🔭 Scanning: {SEARCH_QUERY}...")
    safe_query = urllib.parse.quote(SEARCH_QUERY)
    url = URL_TEMPLATE.format(query=safe_query, loc=LOCATION)
    
    driver.get(url)
    time.sleep(5)

    # --- ROBUST SCROLLING ---
    print("📜 Scrolling to load jobs...")
    for i in range(15): 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3) # Increased wait time
        try:
            # Try finding the "See more jobs" button and clicking it
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "see more jobs" in btn.text.lower():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
        except:
            pass
        if i % 5 == 0: print(f"   -> Scroll {i}/15...")

    # --- EXTRACTION WITH FALLBACKS ---
    cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, li.occludable-update")
    print(f"📊 Found {len(cards)} raw cards. Extracting...")

    all_jobs = []
    for card in cards:
        try:
            # TITLE SELECTORS (Try A, then B)
            title = ""
            try: title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
            except: 
                try: title = card.find_element(By.TAG_NAME, "strong").text
                except: continue # Skip if no title found

            # COMPANY SELECTORS
            company = ""
            try: company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
            except:
                try: company = card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle").text
                except: company = "Unknown"

            # LINK SELECTORS
            link = ""
            try: link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            except: continue

            if link and title:
                if not any(j['Apply Link'] == link for j in all_jobs):
                    all_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link,
                        "Status": "Fresh"
                    })
                    print(f"   -> Found: {title[:30]}...")
        except:
            continue

    # --- SAFE SAVE ---
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        # Filter: Only keep if Title contains key terms (Safety check)
        # Handle cases where 'Job Title' might be missing by ensuring the column exists
        if 'Job Title' in df.columns:
             df = df[df['Job Title'].str.contains('Engineer|Developer|Scientist|Architect|Lead|Data', case=False, na=False)]
        
        df.to_csv(CSV_FILE, index=False)
        print("\n" + "="*50)
        print(f"🎉 SUCCESS: {len(df)} Jobs Saved to '{CSV_FILE}'")
        print("👉 NEXT STEP: python ai_factory.py")
        print("="*50)
    else:
        print("\n❌ CRITICAL: No jobs extracted. The page layout might be different.")

if __name__ == "__main__":
    start_sniper()