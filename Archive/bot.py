import time
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# ---------------------------------------------------------
# 🎯 TARGET ROLES (Matches your Resume)
# ---------------------------------------------------------
TARGET_ROLES = [
    "Machine Learning Engineer", 
    "AI Engineer",
    "Generative AI Engineer",
    "MLOps Engineer",
    "Data Scientist",
    "Analytics Engineer",
    "Forecasting Analyst",
    "Python Automation Engineer",
    "Backend Python Developer",
    "Quantitative Analyst"
]

LOCATION = "India" 
FILENAME = "AIM1000_Master_List.csv"
# ---------------------------------------------------------

def start_bot():
    print("🚀 AIM1000 Bot V4 (Safe-Save) Starting...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("🔑 Logging in...")
        driver.get("https://www.linkedin.com/login")
        input("⚠️ ACTION REQUIRED: Log in to LinkedIn manually, then press Enter here in the terminal...")
    except:
        print("❌ Error during login page load. Check internet.")
        return

    all_jobs = []

    # Loop through EACH role
    for role in TARGET_ROLES:
        print(f"\n🔍 Searching for: {role}...")
        
        try:
            # 1. Navigate to Search Page
            safe_role = urllib.parse.quote(role)
            # Removed the 'Past Week' filter to ensure we get MORE results (Quantity first)
            # f_JT=F means "Full Time"
            # f_WT=2 means "Remote" (Optional: Remove &f_WT=2 if you want hybrid)
            url = f"https://www.linkedin.com/jobs/search/?keywords={safe_role}&location={LOCATION}&f_TPR=r3600
            
            
            driver.get(url)
            time.sleep(3) 

            # 2. Scroll
            print("   📜 Scrolling...")
            for i in range(10): # Scrol 10 times
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # 3. Scrape
            job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, li.occludable-update")
            
            count = 0
            for card in job_cards:
                try:
                    text = card.text.split('\n')
                    if len(text) >= 2:
                        title = text[0]
                        company = text[1]
                        
                        try:
                            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        except:
                            link = "N/A"

                        # Add to list
                        all_jobs.append({
                            "Role Category": role,
                            "Job Title": title,
                            "Company": company,
                            "Apply Link": link
                        })
                        count += 1
                except:
                    continue
            
            print(f"   ✅ Found {count} jobs. (Total so far: {len(all_jobs)})")

            # -------------------------------------------------
            # 🛡️ SAFE SAVE: Save to CSV after EVERY role!
            # -------------------------------------------------
            if all_jobs:
                df = pd.DataFrame(all_jobs)
                df.drop_duplicates(subset=['Apply Link'], inplace=True)
                df.to_csv(FILENAME, index=False)
                print(f"   💾 Saved progress to '{FILENAME}'")
            # -------------------------------------------------

        except WebDriverException:
            print(f"   ⚠️ Network Error on '{role}'. Skipping to next role...")
            time.sleep(5) # Wait for internet to stabilize
            continue
        except Exception as e:
            print(f"   ⚠️ Unknown Error: {e}")
            continue

    print("\n" + "="*40)
    print(f"🎉 FINISHED!")
    print(f"Total Unique Jobs Captured: {len(all_jobs)}")
    print("="*40)

if __name__ == "__main__":
    start_bot()