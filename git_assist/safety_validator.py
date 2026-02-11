class SafetyValidator:

    DANGEROUS = ["delete_branch", "soft_reset"]

    def validate(self, plan):
        DANGEROUS = ["delete_branch", "soft_reset"]
        for action in plan["actions"]:
            if action["type"] in DANGEROUS:
                return False, f"Critical action detected: {action['type']}"
        return True, "Safe to execute"
