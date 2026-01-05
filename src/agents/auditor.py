from typing import Optional

from src.tools import read_file
from src.utils.logger import log_experiment, ActionType


class AuditorAgent:
    def __init__(self, google_api_key: str, model: str = "gemini-1.5") -> None:
        """Create an AuditorAgent and configure the google.generativeai library.

        Args:
            google_api_key: API key for Google Gemini (loaded via dotenv by caller).
            model: Model name to use when calling Gemini.
        """
        self.model = model
        self._genai = None
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=google_api_key)
            self._genai = genai
        except Exception:
            # Library may be missing or configuration failed; keep agent usable for logging
            self._genai = None

    def _extract_text(self, resp) -> str:
        # Best-effort extractor for various client return shapes
        try:
            if resp is None:
                return ""
            # dict-like
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

            # object-like
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
        """Analyze the code at `file_path` using Gemini and return the analysis text.

        The interaction (prompt and response) is logged via `src.utils.logger.log_experiment`
        with `ActionType.ANALYSIS` and must include `input_prompt` and `output_response`.
        """
        code = read_file(file_path)
        prompt = f"Analyze this code and list bugs: {code}"

        analysis: str
        status = "SUCCESS"

        if self._genai is None:
            analysis = "<gemini-unavailable> google.generativeai library not configured or import failed."
            status = "FAILURE"
        else:
            try:
                # Try common client shapes
                if hasattr(self._genai, "generate_text"):
                    resp = self._genai.generate_text(model=self.model, prompt=prompt)
                elif hasattr(self._genai, "chat") and hasattr(self._genai.chat, "create"):
                    resp = self._genai.chat.create(model=self.model, messages=[{"role": "user", "content": prompt}])
                else:
                    # Fallback: attempt a generic call
                    resp = self._genai.generate(model=self.model, prompt=prompt)  # type: ignore

                analysis = self._extract_text(resp)
            except Exception as e:
                analysis = f"<gemini-call-error> {e}"
                status = "FAILURE"

        details = {"input_prompt": prompt, "output_response": analysis}
        try:
            log_experiment("AuditorAgent", self.model, ActionType.ANALYSIS, details, status)
        except Exception:
            # Logging should not raise for the agent's caller; swallow errors
            pass

        return analysis
