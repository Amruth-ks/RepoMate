import os
import sys
from dotenv import load_dotenv

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from git_assist.github_api import GitHubAPI

def test_connection():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not found in .env")
        return

    print(f"Testing GitHub API with token: {token[:4]}...{token[-4:]}")
    api = GitHubAPI(token)
    
    repos = api.get_user_repos()
    if repos:
        print(f"SUCCESS: Successfully fetched {len(repos)} repositories.")
        for r in repos[:3]:
            print(f" - {r['full_name']} (Stars: {r['stargazers_count']})")
    else:
        print("ERROR: Failed to fetch repositories or user has none.")

if __name__ == "__main__":
    test_connection()
