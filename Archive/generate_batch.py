import csv
import os

# ---------------------------------------------------------
# 📝 TEMPLATES (ATS & Recruiter Optimized)
# ---------------------------------------------------------
COVER_LETTER_TEMPLATE = """
Date: {date}

Dear Hiring Team at {company},

I am writing to express my strong interest in the {role} position. As an Applied Machine Learning Engineer with 3+ years of experience, I have successfully built end-to-end IoT prediction systems that process 500k+ daily events—aligning perfectly with the {skill1} and {skill2} requirements at {company}.

Recently, I architected the "Lime IoT ML Platform," a production-grade system that reduced operational risks by 35% through real-time predictive modeling using Python, Docker, and AWS. Unlike standard data science projects, this was a full-lifecycle deployment handling real-world noise and latency constraints.

I am eager to bring this same engineering rigor to {company}.

Sincerely,
Manidhar Pati
[Link to Portfolio/GitHub]
"""

RECRUITER_DM_TEMPLATE = """
Subject: Application for {role} - ML Engineer with Production IoT Experience

Hi {manager},

I just applied for the {role} position and wanted to briefly introduce myself.

I am an ML Engineer specializing in high-frequency IoT data systems. I recently built a production forecasting engine processing 500k+ daily events (Lime Micromobility Project), which matches your team's focus on {skill1}.

You can view the code and architecture here: https://github.com/Manidhar8008/lime-iot-ml-platform-

Best,
Manidhar Pati
"""

# ---------------------------------------------------------
# 🚀 GENERATOR LOGIC
# ---------------------------------------------------------
def generate_applications():
    if not os.path.exists("daily_targets.csv"):
        print("❌ Error: 'daily_targets.csv' not found.")
        return

    print("🚀 Starting Batch Generation...")
    
    with open("daily_targets.csv", "r") as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            company = row['Company'].strip()
            role = row['Role'].strip()
            manager = row['HiringManager'].strip() if row['HiringManager'] else "Hiring Team"
            
            # Create Folder for this Company
            folder_name = f"Apply_{company}_{role}".replace(" ", "_")
            os.makedirs(folder_name, exist_ok=True)
            
            # 1. Generate Cover Letter
            cl_content = COVER_LETTER_TEMPLATE.format(
                date="2025-12-02",
                company=company,
                role=role,
                skill1=row['KeySkill1'],
                skill2=row['KeySkill2']
            )
            with open(f"{folder_name}/Cover_Letter.txt", "w") as f:
                f.write(cl_content.strip())

            # 2. Generate Recruiter DM
            dm_content = RECRUITER_DM_TEMPLATE.format(
                manager=manager,
                role=role,
                skill1=row['KeySkill1']
            )
            with open(f"{folder_name}/Recruiter_DM.txt", "w") as f:
                f.write(dm_content.strip())

            print(f"✅ Generated assets for {company}...")

    print("\n🎉 Batch Complete! Check your folders.")

if __name__ == "__main__":
    generate_applications()