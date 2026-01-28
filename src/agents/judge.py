import os
import time
import subprocess
import shutil
import google.generativeai as genai
from src.utils.logger import log_experiment, ActionType

class JudgeAgent:
    def __init__(self, api_key: str, model: str = "models/gemini-2.5-flash"):
        self.model_name = model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self._test_dir_cleared = False  # Delete test folder only once per program launch

    def generate_tests(self, fixed_code: str) -> str:
        prompt = (
            "You are a Python expert. Generate well-formed Python unit tests using the unittest module.\n"
            "The tests should cover the functionality of the following code. Make sure the tests run without errors.\n\n"
            f"CODE:\n{fixed_code}\n\n"
            "Output ONLY the Python unittest code without markdown blocks."
        )
        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
              
                test_code = response.text.replace("```python", "").replace("```", "").strip().encode("utf-8", "ignore").decode()

                return test_code
            except Exception as e:
                print(f"⚠️ Gemini test generation error ({e}). Retry {attempt+1}/3 in 10s...")
                time.sleep(10)
        return ""

    def run_unit_tests(self, code_path: str, test_path: str) -> dict:
        test_env = os.path.dirname(test_path)
        os.environ["PYTHONPATH"] = test_env

        try:
            result = subprocess.run(
                ["python", "-m", "unittest", os.path.basename(test_path)],
                capture_output=True,
                text=True,
                cwd=test_env
            )
            output = result.stdout + "\n" + result.stderr

            passed, failed = 0, 0
            for line in output.splitlines():
                line = line.strip()
                if line and set(line).issubset({".", "F", "E"}):
                    passed += line.count(".")
                    failed += line.count("F") + line.count("E")

            total = passed + failed
            return {"total": total, "passed": passed, "failed": failed, "output": output}

        except Exception as e:
            return {"total": 0, "passed": 0, "failed": 0, "output": f"<unit-test-run-error> {e}"}

    def judge(self, target_code_path: str, fixer_agent, max_iterations: int = 5, base_dir_override: str = None):
        """
        Main judge loop: generates tests, runs them, and asks fixer for new fixes if needed.
        base_dir_override: optional folder to store test iterations (used for sandbox per file)
        """
        base_dir = base_dir_override if base_dir_override else os.path.join(os.path.dirname(target_code_path), "test")

        # Delete test folder only once per program launch
        if not self._test_dir_cleared and os.path.exists(base_dir):
            shutil.rmtree(base_dir)
            self._test_dir_cleared = True

        os.makedirs(base_dir, exist_ok=True)

        current_code_path = target_code_path
        for iteration in range(1, max_iterations + 1):
            iter_dir = os.path.join(base_dir, f"iteration_{iteration}")
            os.makedirs(iter_dir, exist_ok=True)

            with open(current_code_path, "r") as f:
                fixed_code = f.read()

            test_file_path = os.path.join(iter_dir, "generated_tests.py")
            fixed_file_path = os.path.join(iter_dir, "fixed_code.py")
            next_iter_file_path = os.path.join(iter_dir, "fixed_code_next_iter.py")
            results_file_path = os.path.join(iter_dir, "test_results.txt")

            # Overwrite any existing files
            for path in [test_file_path, fixed_file_path, next_iter_file_path, results_file_path]:
                if os.path.exists(path):
                    os.remove(path)

            test_code = self.generate_tests(fixed_code)
            with open(test_file_path, "w") as f:
                f.write(test_code)

            with open(fixed_file_path, "w") as f:
                f.write(fixed_code)

            results = self.run_unit_tests(fixed_file_path, test_file_path)
            with open(results_file_path, "w") as f:
                f.write(results["output"])

            print(f"Iteration {iteration}: {results['total']} unit tests generated, {results['failed']} failed, {results['passed']} passed")

            if results["failed"] == 0:
                print("✅ All tests passed! Final fixed code accepted.")
                return fixed_file_path

            analysis_plan = f"The following unit tests failed:\n{results['output']}"
            try:
                new_fixed_code = fixer_agent.fix(fixed_code, analysis_plan)
            except Exception as e:
                print(f"⚠️ FixerAgent failed to fix: {e}")
                return fixed_file_path

            with open(next_iter_file_path, "w") as f:
                f.write(new_fixed_code)
            current_code_path = next_iter_file_path

        print(f"⚠️ Maximum iterations ({max_iterations}) reached. Final code may still have failing tests.")
        return current_code_path
