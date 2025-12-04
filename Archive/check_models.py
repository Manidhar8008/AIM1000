import google.generativeai as genai

API_KEY = "AIzaSyAHkLxAcRsHC7O_DMk31kFq0njY3RVuVww"
genai.configure(api_key=API_KEY)

print("🔍 Asking Google for available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ AVAILABLE: {m.name}")
except Exception as e:
    print(f"❌ ERROR: {e}")