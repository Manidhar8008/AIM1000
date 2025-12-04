import schedule
import time
import subprocess
import pandas as pd
import os
from datetime import datetime

# Define Paths
LINKEDIN_BOT = r"D:\AIM1000\Bots\bot.py"
WELLFOUND_BOT = r"D:\AIM1000\Bots\wellfound_bot.py"
MASTER_TRACKER = r"D:\AIM1000\Data\Global_Tracker.csv"

def run_scrapers():
    print(f"\n⏰ [CRON] Starting Hourly Scan: {datetime.now()}")
    
    # 1. Run LinkedIn Bot
    print("   -> Launching LinkedIn Bot...")
    subprocess.run(["python", LINKEDIN_BOT], shell=True)
    
    # 2. Run Wellfound Bot
    print("   -> Launching Wellfound Bot...")
    subprocess.run(["python", WELLFOUND_BOT], shell=True)
    
    # 3. Merge Data (The "Intelligence" Step)
    merge_data()
    
    print("✅ Hourly Scan Complete. Sleeping...")

def merge_data():
    print("   -> Merging Data into Global Tracker...")
    frames = []
    
    # Load LinkedIn Data
    li_path = r"D:\AIM1000\AIM1000_Master_List.csv" # Old path
    if os.path.exists(li_path):
        df_li = pd.read_csv(li_path)
        df_li['Source'] = 'LinkedIn'
        frames.append(df_li)
        
    # Load Wellfound Data
    wf_path = r"D:\AIM1000\Data\Wellfound_Leads.csv"
    if os.path.exists(wf_path):
        df_wf = pd.read_csv(wf_path)
        frames.append(df_wf)
    
    if frames:
        global_df = pd.concat(frames)
        
        # Add tracking columns if missing
        cols = ['Recruiter Message', 'Cover Letter Status', 'Applied Date']
        for c in cols:
            if c not in global_df.columns:
                global_df[c] = "-"
        
        # Remove duplicates
        global_df.drop_duplicates(subset=['Job Title', 'Company'], inplace=True)
        
        global_df.to_csv(MASTER_TRACKER, index=False)
        print(f"   📊 Global Tracker Updated: {len(global_df)} Total Jobs.")

# Schedule: Run every 60 minutes
schedule.every(60).minutes.do(run_scrapers)

# Also run immediately on start
run_scrapers()

while True:
    schedule.run_pending()
    time.sleep(1)