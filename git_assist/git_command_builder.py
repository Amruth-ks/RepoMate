class GitCommandBuilder:

    def build(self, plan):
        commands = []

        for action in plan["actions"]:

            if action["type"] == "stage_all":
                commands.append("git add .")

            elif action["type"] == "commit":
                msg = action.get("message") or "Auto commit"
                commands.append(f'git commit -m "{msg}"')

            elif action["type"] == "push":
                remote = action.get("remote", "origin")
                commands.append(f"git push {remote}")

            elif action["type"] == "pull":
                remote = action.get("remote", "origin")
                commands.append(f"git pull {remote}")

            elif action["type"] == "create_branch":
                commands.append(f"git branch {action['name']}")

            elif action["type"] == "switch_branch":
                commands.append(f"git checkout {action['name']}")

            elif action["type"] == "delete_branch":
                commands.append(f"git branch -d {action['name']}")

            elif action["type"] == "amend_commit":
                commands.append("git commit --amend")

            elif action["type"] == "soft_reset":
                commands.append("git reset --soft HEAD~1")

        return commands
