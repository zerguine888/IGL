import argparse
import sys
import os
from dotenv import load_dotenv

from src.utils.logger import log_experiment, ActionType
from src.tools import read_file, write_file
from src.agents.auditor import AuditorAgent
from src.agents.fixer import FixerAgent


load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True)
    args = parser.parse_args()

    if not os.path.exists(args.target_dir):
        print(f"❌ Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment. Use a .env file or set the variable.")
        sys.exit(1)

    print(f"🚀 DEMARRAGE SUR : {args.target_dir}")

    # Initialize agents
    auditor = AuditorAgent(api_key)
    fixer = FixerAgent(api_key)

    # Log startup
    try:
        log_experiment("System", "local", ActionType.DEBUG, {"input_prompt": "startup", "output_response": f"Target: {args.target_dir}"}, "SUCCESS")
    except Exception:
        pass

    # Walk target dir and process .py files
    for root, _dirs, files in os.walk(args.target_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            full_path = os.path.join(root, fname)
            print(f"Analysing {full_path}...")

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
                fixed = fixer.fix(original_code, analysis)
            except Exception as e:
                fixed = f"<fixer-error> {e}"

            out_name = f"fixed_{os.path.basename(fname)}"
            out_path = os.path.join("sandbox", out_name)
            try:
                write_file(out_path, fixed)
                print(f"Wrote fixed file to {out_path}")
            except Exception as e:
                print(f"Failed to write fixed file {out_path}: {e}")

    print("✅ MISSION_COMPLETE")


if __name__ == "__main__":
    main()