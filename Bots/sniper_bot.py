import time
import pandas as pd
import urllib.parse
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# ⚙️ CONFIGURATION (The "Sniper" Settings)
# ---------------------------------------------------------
TARGET_ROLES = [
    "Machine Learning Engineer",
    "Data Scientist",
    "AI Engineer",
    "Python Developer"
]
LOCATION = "India" # or "United States" or "Worldwide"

# T3 & R1: Force "Past 24 Hours" (r86400) or "Past 1 Hour" (r3600)
# We start with 24h to ensure you get results, but sort by 'Date'
TIME_FILTER = "r86400" 

# HTML Tracker Config
TRACKER_FILE = "Sniper_Mission_Control.html"
CSV_FILE = "Sniper_Fresh_Leads.csv"
# ---------------------------------------------------------

def generate_html_tracker(df):
    """Generates the HTML Dashboard (T2)"""
    html = """
    <html><head><style>
        body { font-family: sans-serif; padding: 20px; background: #1e1e1e; color: #fff; }
        table { width: 100%; border-collapse: collapse; background: #2d2d2d; }
        th, td { padding: 12px; border: 1px solid #444; text-align: left; }
        th { background-color: #0078d4; }
        tr:hover { background-color: #3d3d3d; }
        .btn { background: #28a745; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; }
        .fresh { color: #00ff00; font-weight: bold; }
    </style></head><body>
    <h1>🎯 Sniper Mission Control (Fresh Leads)</h1>
    <table><tr><th>Role</th><th>Company</th><th>Posted</th><th>🚀 Action</th></tr>
    """
    
    for _, row in df.iterrows():
        html += f"""
        <tr>
            <td>{row['Job Title']}</td>
            <td>{row['Company']}</td>
            <td class="fresh">Just Now</td>
            <td><a href="{row['Apply Link']}" target="_blank" class="btn">SNIPE APPLY ↗</a></td>
        </tr>
        """
    html += "</table></body></html>"
    
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Dashboard updated: {TRACKER_FILE}")

def start_sniper():
    print("🚀 SNIPER BOT ACTIVATED...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.linkedin.com/login")
        input("⚠️ ACTION: Log in, then press Enter here...")
    except:
        pass

    all_jobs = []

    for role in TARGET_ROLES:
        print(f"\n🔭 Scanning for Fresh: {role}...")
        
        # URL HACKING for T3 (Remote + Freshness)
        # f_WT=2 (Remote), f_TPR=r86400 (24h), sortBy=DD (Most Recent)
        safe_role = urllib.parse.quote(role)
        url = f"https://www.linkedin.com/jobs/search/?keywords={safe_role}&location={LOCATION}&f_WT=2&f_TPR={TIME_FILTER}&sortBy=DD"
        
        driver.get(url)
        time.sleep(3)
        
        # Quick Scroll
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        
        count = 0
        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
                company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                # Deduplication
                if not any(d['Apply Link'] == link for d in all_jobs):
                    all_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link
                    })
                    count += 1
            except:
                continue
        print(f"   -> Found {count} fresh targets.")

    if all_jobs:
        df = pd.DataFrame(all_jobs)
        df.to_csv(CSV_FILE, index=False)
        generate_html_tracker(df)
        print("\n🎉 SNIPER RUN COMPLETE. OPEN 'Sniper_Mission_Control.html' NOW!")
        
if __name__ == "__main__":
    start_sniper()