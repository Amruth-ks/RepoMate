from git_assist.git_manager import GitManager
import os

print("testing GitManager...")
gm = GitManager(".")

print(f"Repo Path: {gm.repo_path}")

status = gm.get_status()
print("\nStatus:")
for k, v in status.items():
    print(f"  {k}: {v}")

print("\nRunning 'git --version'...")
out, err, code = gm.run_git(["--version"])
print(f"Output: {out}")
