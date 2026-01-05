from src.tools import read_file
from src.utils.logger import log_experiment, ActionType


class AuditorAgent:
    def __init__(self, google_api_key: str, model: str = "models/gemini-1.5"):
        self.model_name = model
        self._genai = None
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=google_api_key)
            self._genai = genai
        except Exception:
            self._genai = None

    def _extract_text(self, resp) -> str:
        try:
            if resp is None:
                return ""
            if isinstance(resp, dict):
                if "candidates" in resp and resp["candidates"]:
                    c = resp["candidates"][0]
                    return c.get("content") or c.get("text") or str(c)
                for key in ("text", "content", "response", "output"):
                    if key in resp:
                        return resp[key] if isinstance(resp[key], str) else str(resp[key])

            for attr in ("text", "content", "output", "response", "candidates"):
                if hasattr(resp, attr):
                    val = getattr(resp, attr)
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list) and val:
                        first = val[0]
                        if isinstance(first, str):
                            return first
                        if isinstance(first, dict) and "content" in first:
                            return first["content"]
                    if isinstance(val, dict) and "content" in val:
                        return val["content"]

            return str(resp)
        except Exception:
            return str(resp)

    def analyze(self, file_path: str) -> str:
        code = read_file(file_path)
        prompt = f"Analyze this code and list bugs:\n\n{code}"

        analysis = ""
        status = "SUCCESS"

        if self._genai is None:
            analysis = "<gemini-unavailable> google.generativeai not installed or failed to configure."
            status = "FAILURE"
        else:
            try:
                if hasattr(self._genai, "generate_text"):
                    resp = self._genai.generate_text(model=self.model_name, prompt=prompt)
                elif hasattr(self._genai, "chat") and hasattr(self._genai.chat, "create"):
                    resp = self._genai.chat.create(model=self.model_name, messages=[{"role": "user", "content": prompt}])
                else:
                    # Last resort: try a generic generate if available
                    resp = getattr(self._genai, "generate", lambda *a, **k: None)(model=self.model_name, prompt=prompt)

                analysis = self._extract_text(resp)
            except Exception as e:
                analysis = f"Error during analysis: {e}"
                status = "FAILURE"

        # Logging obligatoire
        try:
            log_experiment(
                agent_name="AuditorAgent",
                model_used=self.model_name,
                action=ActionType.ANALYSIS,
                details={"input_prompt": prompt, "output_response": analysis},
                status=status,
            )
        except Exception:
            pass

        return analysis