import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

SEARCH_QUERY = "(Python AND (Semiconductor OR IoT OR \"Machine Learning\" OR MLOps))"
LOCATION = "India"
URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}&f_TPR=r86400&f_WT=2&sortBy=DD"
CSV_FILE = "Sniper_Hourly_Leads.csv"
MAX_RETRIES = 3
SCROLL_PAUSE = 2

def start_sniper():
    print("🚀 SNIPER FINAL STARTED...")
    
    options = Options()
    options.page_load_strategy = 'eager'
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    
    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    print(f"\n🔭 Scanning: {SEARCH_QUERY}...")
    safe_query = urllib.parse.quote(SEARCH_QUERY)
    url = URL_TEMPLATE.format(query=safe_query, loc=LOCATION)
    
    driver.get(url)
    time.sleep(6)

    all_jobs = []
    seen_links = set()
    scroll_count = 0
    
    print("📜 Scrolling to load 50+ jobs...")
    
    while len(all_jobs) < 50 and scroll_count < 25:
        scroll_count += 1
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        
        try:
            show_more = driver.find_element(By.CLASS_NAME, "infinite-scroller__show-more-button")
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(1)
        except:
            pass
        
        cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
        print(f"   Scroll {scroll_count}: {len(cards)} cards found...")
        
        for card in cards:
            try:
                title = company = link = ""
                
                try:
                    title = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                except:
                    title = ""
                
                try:
                    company = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                except:
                    company = ""
                
                try:
                    link_elem = card.find_element(By.TAG_NAME, "a")
                    link = link_elem.get_attribute("href")
                    if link:
                        link = link.split("?")[0]
                except:
                    link = ""
                
                # ONLY add if title AND company exist
                if title and company and link and link not in seen_links:
                    seen_links.add(link)
                    all_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link
                    })
                    print(f"      ✅ {company} | {title}")
                    
            except Exception as e:
                continue
        
        if len(all_jobs) >= 50:
            print(f"\n📊 Target reached: {len(all_jobs)} jobs!")
            break
    
    driver.quit()
    
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        # CRITICAL: Drop any NaN rows
        df = df.dropna(subset=['Job Title', 'Company', 'Apply Link'])
        df = df[df['Job Title'].str.strip() != '']
        df = df[df['Company'].str.strip() != '']
        
        df.to_csv(CSV_FILE, index=False)
        print(f"\n✅ SNIPER SUCCESS: {len(df)} clean jobs saved to '{CSV_FILE}'")
        return len(df)
    else:
        print("\n❌ No jobs found.")
        return 0

if __name__ == "__main__":
    start_sniper()