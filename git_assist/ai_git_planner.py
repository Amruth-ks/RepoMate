import openai
import json

SYSTEM_PROMPT = """
You are an intelligent Git assistant.

Convert user instructions into a structured JSON plan containing git command strings.

Rules:
- Output JSON only.
- Do not explain.
- Do not include markdown.
- If multiple steps required, plan sequentially.
- All commands must be git CLI commands (start with "git ").
- Never output non-git shell commands.
- If a commit message is needed but missing, set commit_message to null and use a placeholder commit command.

Output schema:
{
  "commands": ["git ...", "git ..."],
  "commit_message": null
}

Example:

Input:
"Commit my changes and push to origin"

Output:
{
  "commands": [
    "git add -A",
    "git commit -m \"<message>\"",
    "git push origin"
  ],
  "commit_message": null
}
"""

class AIGitPlanner:

    def __init__(self, api_key):
        openai.api_key = api_key

    def generate_plan(self, user_input):
        # Retry with fallback models
        models = ["gpt-4", "gpt-3.5-turbo"]
        last_error = Exception("Unknown AI Error")

        for model in models:
            try:
                print(f"[DEBUG] Requesting Plan from {model}...")
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0
                )

                content = response["choices"][0]["message"]["content"]
                
                # DEBUG: Print raw content
                print(f"[DEBUG] AI Raw Response ({model}): {content}")

                # Clean Markdown
                if content.startswith("```"):
                    content = content.strip("`")
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()

                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    start = content.find("{")
                    end = content.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        return json.loads(content[start : end + 1])
                    raise

            except Exception as e:
                print(f"[WARN] Failed with {model}: {e}")
                last_error = e
                continue # Try next model
        
        # If all failed
        raise last_error

