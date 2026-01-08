import time
import google.generativeai as genai
from src.tools import read_file
from src.utils.logger import log_experiment, ActionType

class AuditorAgent:
    # MISE A JOUR ICI : On utilise le modèle 2.5 disponible dans votre liste
    def __init__(self, google_api_key: str, model: str = "models/gemini-2.5-flash"):
        self.model_name = model
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def analyze(self, file_path: str) -> str:
        code = read_file(file_path)
        prompt = f"Analyze this code and list bugs:\n\n{code}"
        
        analysis = ""
        status = "FAILURE"
        
        # On garde la sécurité anti-crash (Retry)
        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                analysis = response.text
                status = "SUCCESS"
                break 
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Erreur ({error_msg}). Pause de 10s avant réessai {attempt+1}/3...")
                time.sleep(10)

        log_experiment(
            agent_name="AuditorAgent",
            model_used=self.model_name,
            action=ActionType.ANALYSIS,
            details={"input_prompt": prompt, "output_response": analysis},
            status=status
        )
        return analysis