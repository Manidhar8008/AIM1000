import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🎯 SNIPER V7: MEGA-CLUSTER STRATEGY
# ---------------------------------------------------------
# We split your 40+ skills into logical search groups.
# The bot will run 4 separate searches and merge the results.

KEYWORD_CLUSTERS = [
    # Cluster 1: Core ML & Algorithms
    "(Classification OR LSTM OR Prophet OR 'Time-Series' OR 'Anomaly Detection' OR Clustering OR SHAP OR 'Machine Learning')",
    
    # Cluster 2: MLOps & Engineering
    "(MLOps OR Docker OR FastAPI OR Streamlit OR 'GitHub Actions' OR 'Model Registry' OR 'Drift Monitoring')",
    
    # Cluster 3: Cloud & Infrastructure
    "(AWS OR SageMaker OR Lambda OR Athena OR Redshift OR BigQuery OR Azure OR 'CI/CD')",
    
    # Cluster 4: Data Stack & Python
    "(Python AND (Pandas OR NumPy OR SciPy OR SQL OR CTEs OR Tableau OR 'Power BI'))"
]

# FILTERS: Remote (f_WT=2), Past 24h (r86400), Mid-Senior (f_E=4)
# We removed "Easy Apply" from the search to see MORE jobs (we filter later)
URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={query}&location=India&f_WT=2&f_TPR=r86400&f_E=4&sortBy=DD"

CSV_FILE = "Sniper_Mega_Leads.csv"
# ---------------------------------------------------------

def start_sniper():
    print("🚀 SNIPER V7 (MEGA-CLUSTER) ACTIVATED...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    all_jobs = []

    # Loop through each cluster
    for i, query in enumerate(KEYWORD_CLUSTERS):
        print(f"\n🔭 Scanning Cluster {i+1}/{len(KEYWORD_CLUSTERS)}...")
        print(f"   🔎 Query: {query}")
        
        safe_query = urllib.parse.quote(query)
        url = URL_TEMPLATE.format(query=safe_query)
        
        driver.get(url)
        time.sleep(5) 

        # Scroll to load deep results
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        print(f"   📊 Found {len(cards)} cards in this cluster.")

        for card in cards:
            try:
                # Check for Easy Apply tag
                is_easy_apply = "No"
                try:
                    if card.find_elements(By.CSS_SELECTOR, ".job-card-container__footer-item--in-easy-apply"):
                        is_easy_apply = "Yes"
                except:
                    pass

                title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
                company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                # Avoid duplicates across clusters
                if not any(j['Apply Link'] == link for j in all_jobs):
                    all_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Apply Link": link,
                        "Easy Apply": is_easy_apply,
                        "Matched Cluster": f"Cluster {i+1}"
                    })
                    print(f"      + Added: {title}")
            except:
                continue

    # Save Results
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        df = df.sort_values(by='Easy Apply', ascending=False)
        
        try:
            # CRITICAL SAVE FIX
            df.to_csv(CSV_FILE, index=False)
            
            print("\n" + "="*60)
            print(f"🎉 FINAL UNBLOCK SUCCESS. {len(df)} HIGH-MATCH JOBS SAVED.")
            print(f"📂 Saved to: {CSV_FILE}")
            print("👉 NEXT: python ai_tailor_v3.py")
            print("="*60)
            return True
        except Exception as e:
            # Catch file lock errors specifically
            print(f"❌ CRITICAL SAVE ERROR: {e}. Is the CSV file open in Excel?")
            return False
    else:
        print("❌ No jobs found. Try removing 'f_E=4' filter if this persists.")
        return False

