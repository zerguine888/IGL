"""List available Google Gemini models."""
import os

# Try to load dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed, reading env directly")

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY not found in environment.")
    print("   Set it in .env file or as environment variable.")
    exit(1)

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    print("🔍 Listing available Gemini models...\n")
    models = genai.list_models()
    
    for model in models:
        print(f"✓ {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Methods: {model.supported_generation_methods}")
        print()
        
except Exception as e:
    print(f"❌ Error: {e}")
