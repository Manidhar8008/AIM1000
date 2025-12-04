# ...existing code...
import time
import re
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ---------------------------------------------------------
# 🎯 CONFIGURATION: THE "PERFECT MATCH" ENGINE
# ---------------------------------------------------------
# Your Core Stack (From Resume)
USER_SKILLS = {
    "python", "aws", "docker", "kubernetes", "tensorflow", "pytorch",
    "scikit-learn", "sql", "fastapi", "streamlit", "mlops", "ci/cd",
    "airflow", "kafka", "time-series", "lstm", "prophet", "sagemaker",
    "genai", "llm", "rag", "azure", "gcp"
}

BENEFIT_KEYWORDS = {"bonus", "equity", "stock options", "health", "unlimited pto"}

# Thresholds (tweakable)
MIN_SKILLS_STANDARD = 3
MIN_SKILLS_HIGH_COMP = 5

VERBOSE = True
DEBUG_ALL_CSV = "All_Scanned_Jobs_debug.csv"

# Search: Tech Stack (Broad enough to find, strict enough to be relevant)
SEARCH_QUERY = "(Python AND (AWS OR Docker OR MLOps) AND (Machine Learning OR Data))"
LOCATION = "India"

# URL Filters: 
URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}&f_TPR=r86400&f_WT=2&f_E=4&f_AL=true&sortBy=DD"

CSV_FILE = "Sniper_Quality_Leads.csv"
# ---------------------------------------------------------

def normalize_text(s):
    if not s:
        return ""
    s = s.lower()
    # remove punctuation but keep word boundaries
    s = re.sub(r"[^\w\s\-\/]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_jd_text(driver):
    """Try several selectors to reliably extract the job description text."""
    candidates = [
        "#job-details", 
        ".jobs-description__container", 
        ".jobs-description-content__text", 
        ".description__text",
        ".jobs-box__html-content"
    ]
    texts = []
    for sel in candidates:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                t = e.text
                if t and len(t) > 30:
                    texts.append(t)
        except Exception:
            continue
    # fallback: try grabbing any long text on right panel
    if not texts:
        try:
            right_panel = driver.find_element(By.CSS_SELECTOR, ".jobs-details__main-content")
            texts.append(right_panel.text)
        except Exception:
            pass
    combined = "\n".join(texts)
    return normalize_text(combined)

def analyze_job(driver, card):
    """Deep analysis of a single job card (more robust + verbose)."""
    try:
        driver.execute_script("arguments[0].click();", card)
        time.sleep(1.2)  # shorter wait; we gather multiple checks below

        # Title / Company with fallbacks
        title = company = link = ""
        try:
            title = card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
        except:
            try:
                title = card.find_element(By.CSS_SELECTOR, "h3").text
            except:
                title = ""

        try:
            company = card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
        except:
            try:
                company = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name").text
            except:
                company = ""

        try:
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            link = ""

        # Try clicking 'See more' if present
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, ".jobs-description__footer-button, .show-more-less-html__button")
            for b in btns:
                try:
                    b.click()
                    time.sleep(0.4)
                except:
                    pass
        except:
            pass

        jd_text = extract_jd_text(driver)

        # Skill matching using word boundaries to reduce false positives
        skill_matches = 0
        matched_skills = []
        for skill in USER_SKILLS:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, jd_text):
                skill_matches += 1
                matched_skills.append(skill)

        # Benefits
        has_benefits = "No"
        if any(b in jd_text for b in BENEFIT_KEYWORDS):
            has_benefits = "Yes"

        # Applicant Count / Status parsing (more flexible)
        applicant_status = "Standard"
        try:
            top_text = ""
            try:
                top_text = driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__primary-description").text.lower()
            except:
                top_text = driver.find_element(By.CSS_SELECTOR, ".jobs-unified-top-card__subtitle-primary").text.lower()
            if "over" in top_text and "applicant" in top_text:
                applicant_status = "High Competition"
            elif "be one of the first" in top_text or "minutes ago" in top_text or "just posted" in top_text:
                applicant_status = "Early Applicant 🚀"
        except:
            pass

        # Decision matrix (relaxed thresholds)
        keep_job = False
        reason = ""

        if applicant_status == "Early Applicant 🚀":
            keep_job = True
            reason = "Early Bird Advantage"
        elif applicant_status == "High Competition":
            if skill_matches >= MIN_SKILLS_HIGH_COMP:
                keep_job = True
                reason = "High Competition but Strong Match"
            else:
                keep_job = False
        else:
            if skill_matches >= MIN_SKILLS_STANDARD:
                keep_job = True
                reason = "Solid Skill Match"

        # Verbose debug print
        if VERBOSE:
            print(f"   [{company}] {title} | skills={skill_matches} matched={matched_skills} | status={applicant_status}")

        row = {
            "Job Title": title,
            "Company": company,
            "Apply Link": link,
            "Skill Match Count": skill_matches,
            "Matched Skills": ",".join(matched_skills),
            "Applicant Status": applicant_status,
            "Has Benefits": has_benefits,
            "Status": "Quality Lead" if keep_job else "Skipped",
            "Reason": reason,
            "JD Snippet": jd_text[:800]  # keep a snippet for debugging
        }

        return row if keep_job else row

    except Exception as e:
        if VERBOSE:
            print("   ⚠️ analyze_job failed:", e)
        return None

def start_sniper():
    print("🚀 SKILL SNIPER FINAL (QUALITY MODE) ACTIVATED...")

    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'normal'
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://www.linkedin.com/login")
    input("⚠️ ACTION: Log in, then press Enter here...")

    print(f"\n🔭 Scanning High-Value Roles: {SEARCH_QUERY}...")
    safe_query = urllib.parse.quote(SEARCH_QUERY)
    url = URL_TEMPLATE.format(query=safe_query, loc=LOCATION)

    driver.get(url)
    time.sleep(4)

    # Scroll to load jobs
    print("📜 Scrolling to build candidate list...")
    for _ in range(8):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
    print(f"📊 Found {len(cards)} raw cards. Running Quality Analysis...")

    scanned = []
    quality_jobs = []

    for i, card in enumerate(cards):
        row = analyze_job(driver, card)
        if row is None:
            continue
        scanned.append(row)
        if row["Status"] == "Quality Lead":
            # dedupe by link
            if not any(j['Apply Link'] == row['Apply Link'] for j in quality_jobs):
                quality_jobs.append(row)
                print(f"   ✅ KEPT: {row['Job Title']} @ {row['Company']} ({row['Reason']})")

    # Save debug CSV of everything scanned
    if scanned:
        df_all = pd.DataFrame(scanned)
        df_all.to_csv(DEBUG_ALL_CSV, index=False)
        if VERBOSE:
            print(f"📝 Debug: saved all scanned rows to '{DEBUG_ALL_CSV}'")

    # SAVE quality leads
    if quality_jobs:
        df = pd.DataFrame(quality_jobs)

        # Sort by status priority then skill count
        priority = {"Early Applicant 🚀": 0, "Standard": 1, "High Competition": 2}
        df['StatusPriority'] = df['Applicant Status'].map(lambda s: priority.get(s, 3))
        df = df.sort_values(by=['StatusPriority', 'Skill Match Count'], ascending=[True, False]).drop(columns=['StatusPriority'])
        df.to_csv(CSV_FILE, index=False)
        print("\n" + "="*60)
        print(f"🎉 SUCCESS: {len(df)} QUALITY JOBS SAVED TO '{CSV_FILE}'")
        print(f"👉 NEXT STEP: Run 'python ai_factory_v2.py'")
        print("="*60)
    else:
        print("\n❌ No jobs met your high-quality criteria today. Tips:")
        print("   - Check 'All_Scanned_Jobs_debug.csv' to see JD snippets and matches.")
        print("   - Try relaxing thresholds (MIN_SKILLS_STANDARD / MIN_SKILLS_HIGH_COMP) or broaden SEARCH_QUERY.")

if __name__ == "__main__":
    start_sniper()
# ...existing code...