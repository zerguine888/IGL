import argparse
import sys
import os
from dotenv import load_dotenv

from src.utils.logger import log_experiment, ActionType
from src.tools import read_file, write_file
from src.agents.auditor import AuditorAgent
from src.agents.fixer import FixerAgent
from src.agents.judge import JudgeAgent

load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True)
    parser.add_argument("--max_iterations", type=int, default=5, help="Maximum iterations for JudgeAgent")
    args = parser.parse_args()

    if not os.path.exists(args.target_dir):
        print(f"❌ Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment. Use a .env file or set the variable.")
        sys.exit(1)

    print(f"🚀 DEMARRAGE SUR : {args.target_dir}")

    auditor = AuditorAgent(api_key)
    fixer = FixerAgent(api_key)
    judge = JudgeAgent(api_key)

    # Log startup
    try:
        log_experiment("System", "local", ActionType.DEBUG, {"input_prompt": "startup", "output_response": f"Target: {args.target_dir}"}, "SUCCESS")
    except Exception:
        pass

    # Process only original .py files
    for root, _dirs, files in os.walk(args.target_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            if fname.startswith("fixed_") or fname.startswith("fixed_temp_") or fname.startswith("generated_"):
                continue

            full_path = os.path.join(root, fname)
            print(f"\n🔹 Processing {full_path}...")

            try:
                analysis = auditor.analyze(full_path)
            except Exception as e:
                analysis = f"<auditor-error> {e}"

            try:
                original_code = read_file(full_path)
            except Exception as e:
                print(f"Failed to read {full_path}: {e}")
                continue

            try:
                fixed_code = fixer.fix(original_code, analysis)
            except Exception as e:
                print(f"Fixer failed: {e}")
                fixed_code = original_code

            # ✅ Write temp fixed code in sandbox
            sandbox_temp_dir = os.path.join("sandbox", f"temp_{fname}")
            os.makedirs(sandbox_temp_dir, exist_ok=True)
            temp_fixed_path = os.path.join(sandbox_temp_dir, f"fixed_temp_{fname}")
            write_file(temp_fixed_path, fixed_code)

            # ✅ Judge test folder per file: sandbox/temp_<file>/test_<file>
            judge_test_dir = os.path.join(sandbox_temp_dir, f"test_{fname}")
            final_fixed_path = judge.judge(temp_fixed_path, fixer, max_iterations=args.max_iterations, base_dir_override=judge_test_dir)

            # Save final fixed code to sandbox
            sandbox_dir = os.path.join("sandbox")
            os.makedirs(sandbox_dir, exist_ok=True)
            final_output_path = os.path.join(sandbox_dir, f"final_fixed_{fname}")
            write_file(final_output_path, read_file(final_fixed_path))

            print(f"✅ Final fixed code saved to: {final_output_path}")

    print("\n🎯 ALL FILES PROCESSED.")

if __name__ == "__main__":
    main()
