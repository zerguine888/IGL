from typing import Optional

from src.utils.logger import log_experiment, ActionType


class FixerAgent:
    def __init__(self, api_key: str, model: str = "gemini-1.5") -> None:
        """Initialize FixerAgent and configure google.generativeai with `api_key`."""
        self.model = model
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
                if "output" in resp:
                    out = resp["output"]
                    if isinstance(out, dict):
                        return out.get("text") or str(out)
                for key in ("text", "content", "response"):
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
        """Request Gemini to fix `original_code` according to `analysis_plan`.

        Logs the interaction with `log_experiment` using `ActionType.FIX` and
        returns the fixed code as a string.
        """
        prompt = f"Fix this code {original_code} based on this plan {analysis_plan}. Output only the full python code"

        fixed_code = ""
        status = "SUCCESS"

        if self._genai is None:
            fixed_code = "<gemini-unavailable> google.generativeai library not configured or import failed."
            status = "FAILURE"
        else:
            try:
                if hasattr(self._genai, "generate_text"):
                    resp = self._genai.generate_text(model=self.model, prompt=prompt)
                elif hasattr(self._genai, "chat") and hasattr(self._genai.chat, "create"):
                    resp = self._genai.chat.create(model=self.model, messages=[{"role": "user", "content": prompt}])
                else:
                    resp = self._genai.generate(model=self.model, prompt=prompt)  # type: ignore

                fixed_code = self._extract_text(resp)
            except Exception as e:
                fixed_code = f"<gemini-call-error> {e}"
                status = "FAILURE"

        details = {"input_prompt": prompt, "output_response": fixed_code}
        try:
            log_experiment("FixerAgent", self.model, ActionType.FIX, details, status)
        except Exception:
            pass

        return fixed_code
