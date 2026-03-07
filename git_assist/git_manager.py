import subprocess
import os
from .github_api import GitHubAPI

class GitManager:
    def __init__(self, repo_path="."):
        self.repo_path = os.path.abspath(repo_path)
        self.github = GitHubAPI()

    def set_github_token(self, token):
        try:
            if hasattr(self, "github") and self.github is not None:
                self.github.set_token(token)
            else:
                self.github = GitHubAPI(token)
        except Exception:
            self.github = GitHubAPI(token)

    def run_git(self, args):
        """Helper to run git commands."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8', 
                errors='replace'
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except FileNotFoundError:
            return "", "Git not installed", 1
        except Exception as e:
            return "", str(e), 1

    def get_status(self):
        """
        Returns a dict with:
        - initialized: bool
        - remote_connected: bool
        - pending_changes: int
        - files: list of dicts {name, status_code, color}
        - current_branch: str
        """
        status_data = {
            "initialized": False,
            "remote_connected": False,
            "pending_changes": 0,
            "files": [],
            "current_branch": "Unknown"
        }

        # Check if initialized
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            return status_data
        
        status_data["initialized"] = True

        # Get Branch
        out, err, code = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if code == 0:
            status_data["current_branch"] = out

        # Check Remote
        out, _, _ = self.run_git(["remote", "-v"])
        if out:
            status_data["remote_connected"] = True

        # Get File Status
        # ?? - Untracked
        # M  - Modified
        # A  - Added
        # D  - Deleted
        out, _, _ = self.run_git(["status", "--porcelain"])
        
        files = []
        if out:
            lines = out.split("\n")
            status_data["pending_changes"] = len(lines)
            
            for line in lines:
                if not isinstance(line, str) or len(line) < 4: continue
                code = str(line[:2]).strip()
                filename = str(line[3:])
                
                # Determine simple status for UI
                # M = Modified (Yellow), A/?? = Added (Green), D = Deleted (Red)
                color = "#ffc107" # Yellow Default
                if "M" in code:
                    color = "#ffc107" # Yellow
                elif "?" in code or "A" in code:
                    color = "#28a745" # Green
                elif "D" in code:
                    color = "#dc3545" # Red
                
                files.append({
                    "name": filename,
                    "status": code,
                    "color": color
                })
        
        status_data["files"] = files
        return status_data

    def get_branches(self):
        """Returns a list of local branch names."""
        out, _, _ = self.run_git(["branch", "--format=%(refname:short)"])
        if out:
            return out.split("\n")
        return []

    def checkout(self, branch_name):
        """Switch to the specified branch."""
        if not branch_name:
            return False, "Branch name is empty"
        out, err, code = self.run_git(["checkout", branch_name])
        if code == 0:
            return True, out.strip() or f"Switched to '{branch_name}'"
        else:
            return False, err.strip() or f"Failed to switch to '{branch_name}'"

    def run_command(self, args):
        """Standard runner for UI callbacks."""
        return self.run_git(args)[0]

    def execute_commands(self, commands):
        """Executes a list of command strings."""
        results = []
        for cmd in commands:
            # cmd is like "git add ."
            # secure parsing? simplistic for now as per plan
            
            # We need to split by spaces but respect quotes. 
            # Ideally usage of execute_command should pass list of args, 
            # but the planner returns strings.
            # For this prototype, subprocess.run with shell=True is easiest but risky.
            # Let's try to be slightly safer: use shlex or just shell=True for the prototype 
            # since the user is reviewing the commands.
            
            # Actually, the user requirement implies "Executing" what is shown.
            # Since these are git commands, running them in shell is standard for such tools.
            
            try:
                # Using shell=True for windows compatibility with complex commands
                process = subprocess.run(
                    cmd, 
                    cwd=self.repo_path, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                
                status = "SUCCESS" if process.returncode == 0 else "ERROR"
                output = process.stdout if process.returncode == 0 else process.stderr
                
                results.append(f"[{status}] {cmd}\n{output}")
                
                if process.returncode != 0:
                    break # Stop on error
                    
            except Exception as e:
                results.append(f"[ERROR] {cmd}\n{str(e)}")
                break
                
        return results

    def get_staged_diff(self):
        """Return the diff of staged changes."""
        out, _, code = self.run_git(["diff", "--cached"])
        return out if code == 0 else ""

    def clone(self, url, target_dir):
        """Clones a repository into a target directory."""
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(os.getcwd(), target_dir)
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        
        try:
            process = subprocess.run(
                ["git", "clone", url, target_dir],
                capture_output=True,
                text=True,
                check=False
            )
            if process.returncode == 0:
                self.repo_path = target_dir
                return True, f"Successfully cloned {url} to {target_dir}"
            else:
                return False, f"Failed to clone: {process.stderr}"
        except Exception as e:
            return False, str(e)
