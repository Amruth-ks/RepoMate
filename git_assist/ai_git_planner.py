import openai
import json

SYSTEM_PROMPT = """
You are an intelligent Git assistant.

Convert user instructions into structured JSON Git actions.

Rules:
- Output JSON only.
- Do not explain.
- Do not include markdown.
- If multiple steps required, plan sequentially.
- If commit message missing, leave as null.

Supported actions:
- stage_all
- stage_selected
- commit
- push
- pull
- create_branch
- switch_branch
- delete_branch
- amend_commit
- soft_reset

Example:

Input:
"Commit my changes and push to origin"

Output:
{
  "actions": [
    {"type": "stage_all"},
    {"type": "commit", "message": null},
    {"type": "push", "remote": "origin"}
  ]
}
"""

class AIGitPlanner:

    def __init__(self, api_key):
        openai.api_key = api_key

    def generate_plan(self, user_input):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0
        )

        content = response["choices"][0]["message"]["content"]

        return json.loads(content)


class SafetyValidator:

    DANGEROUS = ["delete_branch", "soft_reset"]

    def validate(self, plan):
        DANGEROUS = ["delete_branch", "soft_reset"]
        for action in plan["actions"]:
            if action["type"] in DANGEROUS:
                return False, f"Critical action detected: {action['type']}"
        return True, "Safe to execute"
