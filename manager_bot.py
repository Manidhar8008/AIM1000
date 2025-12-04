import time
import os

print("🤖 AIM1000 AUTOPILOT ENGAGED")
print("   Target: 50+ Jobs/Hour | Auto-Apply with Tailored CVs")
print("---------------------------------------------------")

cycle = 1
while True:
    print(f"\n⏰ CYCLE {cycle} - Starting at {time.strftime('%H:%M:%S')}...")
    
    # 1. Scrape jobs
    print("\n📜 Step 1: Running Sniper Bot...")
    os.system("python sniper_bot_final.py")
    
    # 2. Generate AI-tailored resumes
    print("\n📋 Step 2: Generating AI-Tailored Resumes...")
    os.system("python ai_factory.py")
    
    # 3. Open tracker
    if os.path.exists("Mission_Control.html"):
        try:
            os.startfile(os.path.abspath("Mission_Control.html"))
            print("\n✅ Mission_Control.html opened in browser!")
        except:
            pass
    
    print("\n" + "="*60)
    print("✅ CYCLE COMPLETE")
    print("📱 Share 'Mission_Control.html' to your phone")
    print("👉 Next cycle in 60 minutes...")
    print("="*60)
    
    cycle += 1
    time.sleep(3600)