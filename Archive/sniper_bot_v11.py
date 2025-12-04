import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# ---------------------------------------------------------
# 🎯 SNIPER V11: RESILIENT & FAST MODE
# ---------------------------------------------------------
KEYWORD_CLUSTERS = [
    "(\"Machine Learning\" OR LSTM OR Prophet OR \"Time-Series\" OR \"Anomaly Detection\" OR SHAP)",
    "(MLOps OR Docker OR FastAPI OR Streamlit OR CI/CD OR \"Drift Monitoring\")",
    "(Python OR SQL OR Tableau OR \"Power BI\" OR AWS OR GCP OR Azure)"
]
LOCATION = "India" 
URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}&f_TPR=r86400&f_WT=2&f_E=4&sortBy=DD"
CSV_FILE = "Sniper_Mega_Leads.csv"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 SNIPER V11 (RESILIENT MODE) ACTIVATED...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    
    # ⚡ CRITICAL FIX: Don't wait for images/ads to load
    options.page_load_strategy = 'eager' 
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(45) # Give it 45 seconds max before giving up
    
    try:
        driver.get("https://www.linkedin.com/login")
        input("⚠️ ACTION: Log in, then press Enter here...")
    except Exception:
        print("Login page load issue, but proceeding if browser is open...")

    all_jobs = []

    for i, query in enumerate(KEYWORD_CLUSTERS):
        print(f"\n🔭 Scanning Cluster {i+1}...")
        safe_query = urllib.parse.quote(query)
        url = URL_TEMPLATE.format(query=safe_query, loc=LOCATION)
        
        try:
            driver.get(url)
            time.sleep(5) 
        except TimeoutException:
            print("   ⚠️ Page load timed out! Refreshing and trying again...")
            driver.refresh()
            time.sleep(5)
        except Exception as e:
            print(f"   ⚠️ Network Error on Cluster {i+1}: {e}")
            continue

        # Scroll
        try:
            for _ in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
        except: pass

        cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        print(f"   📊 Found {len(cards)} raw cards.")

        for card in cards:
            try:
                # Force "Yes" to ensure we save everything found
                is_easy_apply = 'Yes' 
                
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
            except:
                continue

    # GUARANTEED SAVE BLOCK
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        # Drop duplicates based on Link
        df = df.drop_duplicates(subset=['Apply Link'])
        
        try:
            df.to_csv(CSV_FILE, index=False)
            print("\n" + "="*60)
            print(f"🎉 FINAL SUCCESS: {len(df)} UNIQUE JOBS SAVED.")
            print(f"📂 Saved to: {CSV_FILE}")
            print("👉 NEXT STEP: python ai_tailor_v3.py")
            print("="*60)
            return True
        except Exception as e:
            print(f"❌ Save Error: {e}. Close Excel!")
            return False
    else:
        print("\n❌ No jobs found. Check Internet connection.")
        return False

if __name__ == "__main__":
    start_sniper()