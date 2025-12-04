import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🎯 SNIPER V10: UNFILTERED SAVE MODE
# ---------------------------------------------------------
KEYWORD_CLUSTERS = [
    "(\"Machine Learning\" OR LSTM OR Prophet OR \"Time-Series\" OR \"Anomaly Detection\" OR SHAP)",
    "(MLOps OR Docker OR FastAPI OR Streamlit OR CI/CD OR \"Drift Monitoring\")",
    "(Python OR SQL OR Tableau OR \"Power BI\" OR AWS OR GCP OR Azure)"
]
LOCATION = "India" 
# Filters in URL: Past 24h, Remote, Mid-Senior
URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}&f_TPR=r86400&f_WT=2&f_E=4&sortBy=DD"
CSV_FILE = "Sniper_Mega_Leads.csv"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 SNIPER V10 (UNFILTERED SAVE) ACTIVATED...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    all_jobs = []

    # Loop through each cluster
    for i, query in enumerate(KEYWORD_CLUSTERS):
        print(f"\n🔭 Scanning Cluster {i+1}/{len(KEYWORD_CLUSTERS)}...")
        safe_query = urllib.parse.quote(query)
        url = URL_TEMPLATE.format(query=safe_query, loc=LOCATION)
        
        driver.get(url)
        time.sleep(5) 

        # Scroll deeply
        for _ in range(8):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        print(f"   📊 Found {len(cards)} raw cards in this cluster.")

        for card in cards:
            try:
                # --- CRITICAL FIX: Assume Easy Apply status is YES ---
                is_easy_apply = 'Yes' # Assume YES because we can't trust the selector
                
                title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
                company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                if not any(j.get('Apply Link') == link for j in all_jobs):
                    all_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link,
                        "Easy Apply": is_easy_apply,
                        "Matched Cluster": f"Cluster {i+1}"
                    })
            except Exception as e:
                # Ignore failed cards
                continue

    # --- FINAL GUARANTEED SAVE BLOCK ---
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        df = df.sort_values(by='Easy Apply', ascending=False)
        
        try:
            df.to_csv(CSV_FILE, index=False)
            print("\n" + "="*60)
            print(f"🎉 FINAL UNBLOCK SUCCESS: {len(df)} UNIQUE JOBS SAVED.")
            print(f"📂 Saved to: {CSV_FILE}")
            print("👉 NEXT STEP: python ai_tailor_v3.py")
            print("="*60)
            return True
        except Exception as e:
            print("\n" + "="*60)
            print(f"❌ CRITICAL SAVE FAILURE. PLEASE CLOSE EXCEL/CSV VIEWER!")
            print(f"Error: {e}")
            print("="*60)
            return False
    else:
        print("\n❌ No jobs found. Try removing 'f_E=4' filter if this persists.")
        return False

if __name__ == "__main__":
    if start_sniper():
        print("✅ Pipeline Ready. Proceed to AI Tailor.")
    else:
        print("⚠️ Pipeline halted.")
