import pandas as pd

# Create dummy data to test the AI
data = [
    {
        "Job Title": "Machine Learning Engineer",
        "Company": "Google",
        "Apply Link": "https://linkedin.com/jobs/view/123",
        "Status": "Fresh"
    },
    {
        "Job Title": "Senior Data Scientist",
        "Company": "Amazon",
        "Apply Link": "https://linkedin.com/jobs/view/456",
        "Status": "Fresh"
    },
    {
        "Job Title": "AI Engineer (GenAI)",
        "Company": "OpenAI",
        "Apply Link": "https://linkedin.com/jobs/view/789",
        "Status": "Fresh"
    }
]

df = pd.DataFrame(data)
df.to_csv("Sniper_EasyApply_Leads.csv", index=False)
print("✅ Test Data Created: 'Sniper_EasyApply_Leads.csv'")
print("👉 You can now run 'python ai_tailor.py'")