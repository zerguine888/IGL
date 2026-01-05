from src.utils.logger import log_experiment, ActionType


class FixerAgent:
    def __init__(self, api_key: str, model: str = "models/gemini-1.5"):
        self.model_name = model
        self._genai = None
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=api_key)
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

    def fix(self, original_code: str, analysis_plan: str) -> str:
        prompt = (
            f"You are a Python expert. Fix the following code based on the analysis plan.\n"
            f"PLAN:\n{analysis_plan}\n\n"
            f"CODE:\n{original_code}\n\n"
            f"Output ONLY the full python code"
        )

        fixed_code = ""
        status = "SUCCESS"

        if self._genai is None:
            fixed_code = "<gemini-unavailable> google.generativeai not installed or failed to configure."
            status = "FAILURE"
        else:
            try:
                if hasattr(self._genai, "generate_text"):
                    resp = self._genai.generate_text(model=self.model_name, prompt=prompt)
                elif hasattr(self._genai, "chat") and hasattr(self._genai.chat, "create"):
                    resp = self._genai.chat.create(model=self.model_name, messages=[{"role": "user", "content": prompt}])
                else:
                    resp = getattr(self._genai, "generate", lambda *a, **k: None)(model=self.model_name, prompt=prompt)

                fixed_code = self._extract_text(resp)
                # basic cleanup
                fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            except Exception as e:
                fixed_code = f"# Error during fix: {e}"
                status = "FAILURE"

        try:
            log_experiment(
                agent_name="FixerAgent",
                model_used=self.model_name,
                action=ActionType.FIX,
                details={"input_prompt": prompt, "output_response": fixed_code},
                status=status,
            )
        except Exception:
            pass

        return fixed_code