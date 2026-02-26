import requests
import os

class GitHubAPI:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def get_user_repos(self):
        """Fetch all repositories for the authenticated user."""
        url = f"{self.base_url}/user/repos"
        try:
            response = requests.get(url, headers=self.headers, params={"sort": "updated", "per_page": 100})
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching repos: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Request exception: {e}")
            return []

    def search_repos(self, query):
        """Search for public repositories."""
        url = f"{self.base_url}/search/repositories"
        try:
            response = requests.get(url, headers=self.headers, params={"q": query, "per_page": 10})
            if response.status_code == 200:
                return response.json().get("items", [])
            else:
                return []
        except Exception as e:
            return []

    def get_repo_details(self, owner, repo):
        """Get details for a specific repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None
