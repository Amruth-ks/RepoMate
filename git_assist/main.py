import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both direct script execution and package-style usage
if __name__ == "__main__" and __package__ is None:
    # If run directly as a script, add the current directory to sys.path
    # so we can use absolute-style imports for sibling modules
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from multilingual_processor import MultilingualProcessor
    from ai_git_planner import AIGitPlanner
    from safety_validator import SafetyValidator
else:
    # If imported as a package or run with python -m
    try:
        from .multilingual_processor import MultilingualProcessor
        from .ai_git_planner import AIGitPlanner
        from .safety_validator import SafetyValidator
    except (ImportError, ValueError):
        try:
            from git_assist.multilingual_processor import MultilingualProcessor
            from git_assist.ai_git_planner import AIGitPlanner
            from git_assist.safety_validator import SafetyValidator
        except ImportError:
            from multilingual_processor import MultilingualProcessor
            from ai_git_planner import AIGitPlanner
            from safety_validator import SafetyValidator

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found in .env file.")
    print("Please create a .env file with OPENAI_API_KEY=sk-...")

processor = MultilingualProcessor()
planner = AIGitPlanner(API_KEY)
validator = SafetyValidator()

def run(text=None):
    if text:
        user_input = text
    else:
        user_input = input("Enter Git instruction: ")

    # Step 1: Normalize language
    normalized_text, detected_lang = processor.normalize(user_input)
    print(f"\nDetected language: {detected_lang}")
    print(f"Normalized: {normalized_text}")

    # Step 2: Generate structured plan
    plan = planner.generate_plan(normalized_text)
    print("\nGenerated Plan:")
    print(plan)

    # Step 3: Validate safety
    safe, message = validator.validate(plan)
    print("\nSafety Check:", message)

    if not safe:
        print("Execution stopped.")
        return

    # Step 4: Commands are generated directly by the planner
    commands = plan.get("commands", [])

    print("\nGenerated Git Commands:")
    for cmd in commands:
        print(cmd)

if __name__ == "__main__":
    run()
