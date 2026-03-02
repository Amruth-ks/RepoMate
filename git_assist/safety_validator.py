class SafetyValidator:

    DANGEROUS_SUBSTRINGS = [
        " reset ",
        " reset--",
        " reset -",
        " clean",
        " checkout --",
        " restore --",
        " branch -D",
        " push --force",
        " push -f",
        " rm ",
    ]

    def validate(self, plan):
        if not isinstance(plan, dict):
            return False, "Invalid plan format"

        commands = plan.get("commands")
        if not isinstance(commands, list) or not commands:
            return False, "Plan must contain a non-empty 'commands' list"

        for cmd in commands:
            if not isinstance(cmd, str) or not cmd.strip():
                return False, "Plan contains an invalid command"

            normalized = " " + cmd.strip().lower() + " "
            if not normalized.strip().startswith("git "):
                return False, "Only git commands are allowed"

            for bad in self.DANGEROUS_SUBSTRINGS:
                if bad in normalized:
                    return False, f"Blocked potentially dangerous command: {cmd}"

        return True, "Safe to execute"
