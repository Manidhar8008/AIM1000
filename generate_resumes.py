# ...existing code...
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

CSV_FILE = "Sniper_Hourly_Leads.csv"
TRACKER_FILE = "Mission_Control.html"
RESUME_DIR = "resumes"
CANDIDATE_NAME = "Manidhar"   # adjust as needed
BASE_SKILLS = ["Python", "Machine Learning", "AWS", "Docker", "Kubernetes", "SQL", "MLOps"]

os.makedirs(RESUME_DIR, exist_ok=True)

def sanitize(s):
    return "".join(c for c in str(s) if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")[:60]

def build_pdf(filename, job_title, company, extra_notes=""):
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4
    margin = 20*mm
    y = h - margin

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, CANDIDATE_NAME)
    c.setFont("Helvetica", 10)
    c.drawString(margin + 120*mm, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 12*mm

    # Title / target
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, f"Target Role: {job_title}  |  {company}")
    y -= 10*mm

    # Summary
    c.setFont("Helvetica", 11)
    summary = f"Tailored summary: Experienced in {', '.join(BASE_SKILLS[:4])}. This resume is adjusted for the role of {job_title} at {company}."
    text = c.beginText(margin, y)
    text.setLeading(12)
    text.textLines(summary)
    c.drawText(text)
    y -= 20*mm

    # Skills
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Key Skills")
    y -= 8*mm
    c.setFont("Helvetica", 11)
    skills_text = ", ".join(BASE_SKILLS)
    c.drawString(margin, y, skills_text)
    y -= 15*mm

    # Experience placeholder
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Experience (highlights)")
    y -= 8*mm
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, "- Relevant work and projects tailored to the job requirements.")
    y -= 10*mm
    c.drawString(margin, y, extra_notes[:600])

    c.showPage()
    c.save()

def main():
    if not os.path.exists(CSV_FILE):
        print(f"CSV not found: {CSV_FILE}  — run the sniper first.")
        return

    df = pd.read_csv(CSV_FILE)
    if df.empty:
        print("No jobs in CSV.")
        return

    rows_for_html = []
    for i, row in df.iterrows():
        title = row.get("Job Title", "Role")
        company = row.get("Company", "Company")
        link = row.get("Apply Link", "#")

        safe_name = sanitize(f"{company}_{title}_{i}")
        pdf_name = f"{CANDIDATE_NAME}_{safe_name}.pdf"
        pdf_path = os.path.join(RESUME_DIR, pdf_name)

        # Create a simple tailored PDF
        extra = f"Tailored for {title} at {company}."
        try:
            build_pdf(pdf_path, title, company, extra_notes=extra)
        except Exception as e:
            print("PDF generation failed for", title, company, e)
            continue

        rows_for_html.append({
            "Job Title": title,
            "Company": company,
            "Apply Link": link,
            "Resume Path": pdf_path
        })

    # Build Mission_Control.html
    html = []
    html.append("<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>")
    html.append("<style>body{font-family:sans-serif;padding:10px;background:#f3f2ef}table{width:100%;border-collapse:collapse}th,td{padding:8px;border:1px solid #ddd;text-align:left}th{background:#004182;color:#fff}</style>")
    html.append("<title>Mission Control</title></head><body>")
    html.append(f"<h2>🚀 Mission Control — {datetime.now().strftime('%Y-%m-%d %H:%M')}</h2>")
    html.append("<p>Tap the APPLY link to open job page. Tap the DOWNLOAD link to save the tailored CV on your device.</p>")
    html.append("<table><tr><th>Company</th><th>Role</th><th>Apply</th><th>Download CV</th></tr>")

    for r in rows_for_html:
        apply_link = r["Apply Link"]
        resume_rel = os.path.relpath(r["Resume Path"], os.path.dirname(TRACKER_FILE))
        # for mobile: make resume path absolute file:// URL if needed
        resume_url = f"{resume_rel}"
        html.append(f"<tr><td>{r['Company']}</td><td>{r['Job Title']}</td>"
                    f"<td><a href='{apply_link}' target='_blank'>APPLY ↗</a></td>"
                    f"<td><a href='{resume_url}' download>DOWNLOAD CV ↧</a></td></tr>")

    html.append("</table>")
    html.append("<p>Tip: To use on phone, transfer the Mission_Control.html and the 'resumes' folder to your phone, or host the folder (e.g., GitHub Pages / simple file server).</p>")
    html.append("</body></html>")

    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    print(f"Generated {len(rows_for_html)} resumes in '{RESUME_DIR}' and tracker '{TRACKER_FILE}'")
    # open tracker on Windows
    try:
        os.startfile(os.path.abspath(TRACKER_FILE))
    except:
        pass

if __name__ == "__main__":
    main()
# ...existing code...