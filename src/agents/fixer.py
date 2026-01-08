import time
import google.generativeai as genai
from src.utils.logger import log_experiment, ActionType

class FixerAgent:
    # MISE A JOUR ICI : On utilise le modèle 2.5
    def __init__(self, api_key: str, model: str = "models/gemini-2.5-flash"):
        self.model_name = model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def fix(self, original_code: str, analysis_plan: str) -> str:
        prompt = (
            f"You are a Python expert. Fix the following code based on the analysis plan.\n"
            f"PLAN:\n{analysis_plan}\n\n"
            f"CODE:\n{original_code}\n\n"
            f"Output ONLY the fixed Python code without markdown blocks."
        )

        fixed_code = ""
        status = "FAILURE"

        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                # Nettoyage automatique du markdown
                fixed_code = response.text.replace("```python", "").replace("```", "").strip()
                status = "SUCCESS"
                break
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Erreur ({error_msg}). Pause de 10s avant réessai {attempt+1}/3...")
                time.sleep(10)

        log_experiment(
            agent_name="FixerAgent",
            model_used=self.model_name,
            action=ActionType.FIX,
            details={"input_prompt": prompt, "output_response": fixed_code},
            status=status
        )
        return fixed_code