import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime

# ---------------------------------------------------------
# 🎯 SEARCH STRATEGY (Multi-Technique)
# ---------------------------------------------------------
SEARCH_CONFIGS = [
    # Technique 1: Core Tech Stack
    {
        "query": "(Python OR \"Machine Learning\" OR MLOps) AND (AWS OR Docker OR Kubernetes)",
        "filters": {"remote": True, "level": "senior", "salary": "30-40 LPA"}
    },
    # Technique 2: Job Title Focus
    {
        "query": "\"Data Scientist\" OR \"ML Engineer\" OR \"MLOps Engineer\" OR \"ML Ops\"",
        "filters": {"remote": True, "level": "mid-senior", "salary": "30-40 LPA"}
    },
    # Technique 3: Skills Focus
    {
        "query": "(TensorFlow OR PyTorch OR \"Scikit-learn\") AND (Python AND AWS)",
        "filters": {"remote": True, "level": "senior"}
    },
    # Technique 4: Industry Focus
    {
        "query": "\"Data Science\" AND (Bangalore OR \"India Remote\")",
        "filters": {"remote": True, "employment_type": "full-time"}
    },
    # Technique 5: KPI/Outcome Focus
    {
        "query": "(\"Model Deployment\" OR \"Production ML\" OR \"Data Pipeline\") AND Python",
        "filters": {"remote": True, "level": "mid-senior"}
    }
]

OUTPUT_CSV = "output/Turbo_Leads.csv"
MAX_JOBS_PER_SEARCH = 50  # Target 50 per search × 5 searches = 250 jobs
BATCH_DELAY = 3600  # 1 hour between batches

# ---------------------------------------------------------

def scrape_with_technique(driver, search_config, batch_num):
    """Scrape using one search technique"""
    query = search_config["query"]
    filters = search_config["filters"]
    
    print(f"\n🔍 [BATCH {batch_num}] Technique: {query[:50]}...")
    
    # Build URL with all filters
    safe_query = urllib.parse.quote(query)
    url = f"https://www.linkedin.com/jobs/search/?keywords={safe_query}&location=India&f_TP=1&f_WT=2&f_E=3,4,5"
    
    # Add salary filter if present
    if "salary" in filters:
        # LinkedIn salary codes: 30-40 LPA ≈ $3600-4800/mo
        url += "&f_S=1"  # Salary provided
    
    driver.get(url)
    time.sleep(4)
    
    jobs = []
    seen_links = set()
    
    # Aggressive scrolling
    for scroll_iteration in range(15):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, ".infinite-scroller__show-more-button")
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(1)
        except:
            pass
    
    # Extract all cards
    cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
    print(f"   📊 Found {len(cards)} cards. Extracting...")
    
    for card_idx, card in enumerate(cards):
        if len(jobs) >= MAX_JOBS_PER_SEARCH:
            break
        
        try:
            # Title
            title = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
            
            # Company
            company = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
            
            # Link
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            if link:
                link = link.split("?")[0]
            
            # Job description snippet (for keyword matching)
            jd_snippet = ""
            try:
                jd_snippet = card.find_element(By.CSS_SELECTOR, ".base-search-card__snippet").text
            except:
                pass
            
            # Check if meets criteria (70% match rule)
            if meets_criteria(title, company, jd_snippet):
                if link not in seen_links:
                    seen_links.add(link)
                    jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link,
                        "JD Snippet": jd_snippet,
                        "Search Technique": query[:40],
                        "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    print(f"      ✅ {company} | {title}")
        
        except Exception as e:
            continue
    
    return jobs

def meets_criteria(title, company, jd_snippet):
    """70% match rule: Check if job meets minimum criteria"""
    criteria = {
        "remote": ["remote", "work from home", "wfh", "distributed"],
        "fulltime": ["full-time", "full time", "fulltime"],
        "salary_bracket": ["30", "40", "lpa", "₹", "rupee"],
        "benefits": ["health", "bonus", "equity", "stock", "pto"],
        "data_science": ["data scientist", "ml engineer", "machine learning", "data engineer", "analytics"]
    }
    
    combined_text = f"{title} {company} {jd_snippet}".lower()
    
    matches = 0
    total_rules = 5
    
    if any(word in combined_text for word in criteria["remote"]):
        matches += 1
    if any(word in combined_text for word in criteria["fulltime"]):
        matches += 1
    if any(word in combined_text for word in criteria["salary_bracket"]):
        matches += 1
    if any(word in combined_text for word in criteria["benefits"]):
        matches += 1
    if any(word in combined_text for word in criteria["data_science"]):
        matches += 1
    
    match_percentage = (matches / total_rules) * 100
    return match_percentage >= 70

def main():
    print("🚀 TURBO SNIPER V3 STARTED (Multi-Technique)")
    
    options = Options()
    options.page_load_strategy = 'eager'
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    driver.get("https://www.linkedin.com/login")
    input("⚠️ Login to LinkedIn, then press Enter...")
    
    os.makedirs("output", exist_ok=True)
    
    all_jobs = []
    
    for batch_num, config in enumerate(SEARCH_CONFIGS, 1):
        batch_jobs = scrape_with_technique(driver, config, batch_num)
        all_jobs.extend(batch_jobs)
        print(f"   📈 Total so far: {len(all_jobs)} jobs")
        time.sleep(2)
    
    driver.quit()
    
    # Deduplicate by link
    df = pd.DataFrame(all_jobs)
    df = df.drop_duplicates(subset=['Apply Link'])
    
    # Clean
    df = df.dropna(subset=['Job Title', 'Company'])
    df = df[df['Job Title'].str.strip() != '']
    df = df[df['Company'].str.strip() != '']
    
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ TURBO SNIPER COMPLETE: {len(df)} unique jobs saved to '{OUTPUT_CSV}'")
    return len(df)

if __name__ == "__main__":
    import os
    main()