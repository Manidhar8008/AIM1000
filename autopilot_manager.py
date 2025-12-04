import time
import os

print("🤖 AIM1000 AUTOPILOT ENGAGED")
print("   Cycle: Hourly Scrape & Generate")
print("--------------------------------")

while True:
    print(f"\n⏰ Starting Cycle at {time.strftime('%H:%M')}...")
    
    # 1. Run Sniper
    os.system("python turbo_sniper_v3.py")
    
    # 2. Run AI Factory
    os.system("python ai_factory_v2.py")
    
    print("✅ Cycle Complete. Sleeping for 60 minutes...")
    time.sleep(3600)