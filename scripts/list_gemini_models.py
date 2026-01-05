"""Attempt to list available Google Gemini models using the installed
google.generativeai package and the `GOOGLE_API_KEY` environment variable.

This script prints either the models or a helpful error message.
"""
import os
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(path='.env'):
        # Minimal fallback: parse simple KEY=VALUE lines
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not set in environment (.env missing or variable unset).")
        return

    try:
        import google.generativeai as genai  # type: ignore
    except Exception as e:
        print(f"google.generativeai import failed: {e}")
        return

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"genai.configure failed: {e}")

    # Try common listing method(s)
    tried = False
    try:
        if hasattr(genai, "list_models"):
            tried = True
            models = genai.list_models()
            print("list_models() result:\n", models)
    except Exception as e:
        print(f"list_models() call failed: {e}")

    try:
        if not tried and hasattr(genai, "models"):
            # Some versions expose a models client
            tried = True
            print("genai.models available; attempting genai.models.list()")
            models = genai.models.list()
            print(models)
    except Exception as e:
        print(f"genai.models.list() call failed: {e}")

    if not tried:
        print("Could not find a supported 'list models' method on google.generativeai.")


if __name__ == "__main__":
    main()
