import time
import urllib.parse
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# MULTI-STRATEGY SEARCH CONFIG
# ---------------------------------------------------------
SEARCH_STRATEGIES = [
    # Strategy 1: Data Science + Remote + Full-time
    {
        "query": "(Data Science OR Machine Learning OR MLOps) AND (Remote OR Work from home) AND Python",
        "location": "India"
    },
    # Strategy 2: IoT + Semiconductor + ML
    {
        "query": "(IoT OR Embedded OR Semiconductor) AND (Machine Learning OR Python) AND Remote",
        "location": "India"
    },
    # Strategy 3: Data Engineering + Analytics
    {
        "query": "(Data Engineering OR Analytics OR Big Data) AND (Python OR Spark) AND Remote",
        "location": "India"
    },
    # Strategy 4: AI/ML Engineer roles
    {
        "query": "\"AI Engineer\" OR \"ML Engineer\" OR \"Data Scientist\" Remote Full-time",
        "location": "India"
    },
]

# Satisfaction Rules (70% match required)
MUST_HAVE = {
    "remote": ["remote", "work from home", "wfh"],
    "full_time": ["full-time", "full time", "ft"],
    "salary": ["30", "40", "50", "lpa", "lakhs"],  # 30-40 LPA bracket
}

NICE_TO_HAVE = {
    "benefits": ["health", "bonus", "equity", "pto", "insurance"],
    "data_science": ["data science", "machine learning", "nlp", "cv", "deep learning"],
}

TECH_STACK = ["python", "aws", "docker", "kubernetes", "tensorflow", "pytorch", "sql"]

CSV_FILE = "Sniper_Hourly_Leads.csv"
BATCH_SIZE = 15
SCROLL_PAUSE = 1.5

def calculate_match_score(jd_text, title, company):
    """Calculate 70% match score based on rules"""
    jd_lower = jd_text.lower()
    title_lower = title.lower()
    
    score = 0
    max_score = 10
    
    # Must have: Remote (2 points)
    if any(r in jd_lower for r in MUST_HAVE["remote"]) or any(r in title_lower for r in MUST_HAVE["remote"]):
        score += 2
    
    # Must have: Full-time (2 points)
    if any(ft in jd_lower for ft in MUST_HAVE["full_time"]) or "full" in title_lower:
        score += 2
    
    # Must have: Salary bracket (2 points)
    if any(sal in jd_lower for sal in MUST_HAVE["salary"]):
        score += 2
    
    # Nice to have: Data Science background (2 points)
    if any(ds in jd_lower for ds in NICE_TO_HAVE["data_science"]):
        score += 2
    
    # Nice to have: Benefits (1 point)
    if any(b in jd_lower for b in NICE_TO_HAVE["benefits"]):
        score += 1
    
    # Tech stack match (1 point per 2 skills found, max 1)
    tech_matches = sum(1 for tech in TECH_STACK if tech in jd_lower)
    if tech_matches >= 2:
        score += 1
    
    match_percentage = (score / max_score) * 100
    return match_percentage, score

def extract_jd_text(driver):
    """Extract job description safely"""
    selectors = [
        "#job-details",
        ".jobs-description__container",
        ".show-more-less-html__markup",
    ]
    texts = []
    for sel in selectors:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, sel)
            texts.append(elem.text)
        except:
            pass
    return "\n".join(texts).lower() if texts else ""

def scrape_strategy(driver, search_config):
    """Scrape jobs using one search strategy"""
    query = search_config["query"]
    location = search_config["location"]
    
    print(f"\n🔍 Strategy: {query[:50]}...")
    safe_query = urllib.parse.quote(query)
    url = f"https://www.linkedin.com/jobs/search/?keywords={safe_query}&location={location}&f_WT=2&f_E=2,3,4&sortBy=DD"
    
    driver.get(url)
    time.sleep(4)
    
    jobs = []
    seen_links = set()
    scroll_count = 0
    
    while len(jobs) < BATCH_SIZE and scroll_count < 15:
        scroll_count += 1
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        
        try:
            show_more = driver.find_element(By.CLASS_NAME, "infinite-scroller__show-more-button")
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(0.8)
        except:
            pass
        
        cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
        
        for card in cards:
            try:
                # Extract title, company, link
                title = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                company = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href").split("?")[0]
                
                if link in seen_links or not (title and company and link):
                    continue
                
                # Click to get JD
                driver.execute_script("arguments[0].click();", card)
                time.sleep(1.2)
                
                jd_text = extract_jd_text(driver)
                
                # Calculate match score
                match_pct, match_score = calculate_match_score(jd_text, title, company)
                
                # 70% threshold = 7/10 score
                if match_pct >= 70:
                    seen_links.add(link)
                    jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link,
                        "Match Score": f"{match_pct:.0f}%",
                        "Match Details": f"{match_score}/10",
                        "JD Snippet": jd_text[:500]
                    })
                    print(f"   ✅ {company} | {title} | Match: {match_pct:.0f}%")
                else:
                    print(f"   ⏭️ {company} | {title} | Low match: {match_pct:.0f}% (need 70%+)")
                    
            except Exception as e:
                continue
    
    return jobs

def main():
    print("🚀 SNIPER V4 - MULTI-STRATEGY SEARCH")
    
    options = Options()
    options.page_load_strategy = 'eager'
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    driver.get("https://www.linkedin.com/login")
    input("⚠️ Log in, then press Enter...")
    
    all_jobs = []
    
    for strategy in SEARCH_STRATEGIES:
        jobs = scrape_strategy(driver, strategy)
        all_jobs.extend(jobs)
        print(f"   📊 Total so far: {len(all_jobs)}")
        if len(all_jobs) >= BATCH_SIZE:
            break
    
    driver.quit()
    
    # Save to CSV
    if all_jobs:
        df = pd.DataFrame(all_jobs).drop_duplicates(subset=['Apply Link'])
        df = df.head(BATCH_SIZE)  # Take top BATCH_SIZE
        df.to_csv(CSV_FILE, index=False)
        print(f"\n✅ SAVED: {len(df)} jobs to '{CSV_FILE}'")
    else:
        print("\n❌ No jobs found.")

if __name__ == "__main__":
    main()