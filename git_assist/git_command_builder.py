class GitCommandBuilder:

    def build(self, plan):
        if not isinstance(plan, dict):
            raise ValueError("Invalid plan: expected an object with an 'actions' list")

        actions = plan.get("actions")
        if not isinstance(actions, list):
            raise ValueError("Invalid plan: missing or invalid 'actions' list")

        commands = []
        staged_since_last_commit = False
        for idx, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ValueError(f"Invalid action at index {idx}: expected object")

            action_type = action.get("type")
            if not isinstance(action_type, str) or not action_type:
                raise ValueError(f"Invalid action at index {idx}: missing 'type'")

            if action_type == "stage_all":
                commands.append("git add -A")
                staged_since_last_commit = True

            elif action_type == "stage_selected":
                files = action.get("files")
                if not isinstance(files, list) or not all(isinstance(f, str) and f for f in files):
                    raise ValueError("stage_selected requires a non-empty 'files' string list")
                for f in files:
                    commands.append(f'git add -- "{f}"')
                staged_since_last_commit = True

            elif action_type == "commit":
                if not staged_since_last_commit:
                    commands.append("git add -A")
                msg = action.get("message") or "Auto commit"
                msg = str(msg).replace('"', '\\"')
                commands.append(f'git commit -m "{msg}"')
                staged_since_last_commit = False

            elif action_type == "push":
                remote = action.get("remote", "origin")
                branch = action.get("branch")
                set_upstream = bool(action.get("set_upstream"))
                if branch:
                    if set_upstream:
                        commands.append(f"git push -u {remote} {branch}")
                    else:
                        commands.append(f"git push {remote} {branch}")
                else:
                    commands.append(f"git push {remote}")

            elif action_type == "pull":
                remote = action.get("remote", "origin")
                branch = action.get("branch")
                if branch:
                    commands.append(f"git pull {remote} {branch}")
                else:
                    commands.append(f"git pull {remote}")

            elif action_type == "create_branch":
                name = action.get("name")
                if not isinstance(name, str) or not name:
                    raise ValueError("create_branch requires 'name'")
                should_switch = action.get("switch", True)
                if should_switch:
                    commands.append(f"git switch -c {name}")
                else:
                    commands.append(f"git branch {name}")

            elif action_type == "switch_branch":
                name = action.get("name")
                if not isinstance(name, str) or not name:
                    raise ValueError("switch_branch requires 'name'")
                commands.append(f"git switch {name}")

            elif action_type == "delete_branch":
                name = action.get("name")
                if not isinstance(name, str) or not name:
                    raise ValueError("delete_branch requires 'name'")
                commands.append(f"git branch -d {name}")

            elif action_type == "amend_commit":
                commands.append("git commit --amend")

            elif action_type == "soft_reset":
                commands.append("git reset --soft HEAD~1")

            elif action_type in {"status", "git_status", "git status"}:
                commands.append("git status")

            else:
                raise ValueError(f"Unsupported action type: {action_type}")

        return commands
