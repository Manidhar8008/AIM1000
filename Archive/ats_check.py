import PyPDF2
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------
# ⚙️ CONFIGURATION
# ---------------------------------------------------------
CV_FILENAME = "Manidhar_pati_CV 2026.pdf"  # Make sure your PDF is in the folder!
# ---------------------------------------------------------

def clean_text(text):
    # Convert to lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except FileNotFoundError:
        print(f"❌ ERROR: Could not find '{pdf_path}'.")
        print("   -> Please put your PDF resume in the 'D:\\AIM1000' folder.")
        return None

def calculate_match_score(cv_text, jd_text):
    # Combine texts to create a vocabulary
    corpus = [cv_text, jd_text]
    
    # Use CountVectorizer to convert text to vectors (Keyword counting)
    vectorizer = CountVectorizer(stop_words='english')
    count_matrix = vectorizer.fit_transform(corpus)
    
    # Calculate Cosine Similarity (How similar are the two vectors?)
    matchPercentage = cosine_similarity(count_matrix)[0][1] * 100
    matchPercentage = round(matchPercentage, 2)
    
    # Find Missing Keywords
    feature_names = vectorizer.get_feature_names_out()
    cv_vector = count_matrix.toarray()[0]
    jd_vector = count_matrix.toarray()[1]
    
    missing_keywords = []
    for i, word in enumerate(feature_names):
        # If word is in JD (value > 0) but NOT in CV (value == 0)
        if jd_vector[i] > 0 and cv_vector[i] == 0:
            missing_keywords.append(word)
            
    return matchPercentage, missing_keywords

def start_ats_check():
    print("🚀 AIM1000: Personal ATS Scanner Starting...")
    
    # 1. Read CV
    print(f"📄 Reading '{CV_FILENAME}'...")
    cv_text = extract_text_from_pdf(CV_FILENAME)
    if not cv_text: return
    
    cv_clean = clean_text(cv_text)
    print("✅ CV Loaded Successfully!")

    while True:
        print("\n" + "="*50)
        print("🎯 PASTE A JOB DESCRIPTION BELOW (Press Ctrl+Z then Enter to finish):")
        print("="*50)
        
        # Capture Multi-line Input
        try:
            lines = []
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass # Creating a break point for the input
            
        jd_text = " ".join(lines)
        
        if len(jd_text) < 50:
            print("⚠️ JD too short. Please try again.")
            continue

        # 2. Analyze
        jd_clean = clean_text(jd_text)
        score, missing = calculate_match_score(cv_clean, jd_clean)

        # 3. Report
        print("\n" + "-"*30)
        print(f"📊 FIT SCORE: {score}%")
        print("-"*30)
        
        if score > 75:
            print("✅ EXCELLENT MATCH! You should apply immediately.")
        elif score > 50:
            print("⚠️ GOOD MATCH, BUT MISSING KEYWORDS.")
        else:
            print("❌ LOW MATCH. Do not apply without editing.")

        print("\n🔍 MISSING KEYWORDS (Top 10):")
        # Filter strictly for tech terms to avoid noise (basic filter)
        tech_filter = [w for w in missing if len(w) > 3][:15] 
        print(", ".join(tech_filter))
        
        print("\n👉 ACTION: Add these words to your CV summary or skills section.")

if __name__ == "__main__":
    start_ats_check()