import json
import openai # Or use google-genai / anthropic based on your LLM provider

SYSTEM_PROMPT = """
You are a Staff Software Engineer performing an automated Code Review on a Git Diff.
Your goal is to provide concise, high-value code suggestions.

Focus on:
1. Critical bugs, memory leaks, or race conditions
2. Security issues or hardcoded secrets
3. Performance bottlenecks or anti-patterns
4. Code clarity and dead code removal

RULES FOR INLINE COMMENTS:
- Provide comments ONLY for changed lines (lines starting with '+' or '-').
- Ignore auto-generated files (e.g., .xcuserstate, lockfiles, xcodeproj).
- Keep overall comments focused and constructive.

You MUST reply ONLY with a JSON object strictly following this format:
{
  "summary": "Short 2-3 sentence overview of the pull request changes.",
  "comments": [
    {
      "path": "path/to/file.swift",
      "line": 38,
      "body": "Clear, actionable recommendation or suggestion."
    }
  ]
}
"""

class AIReviewer:
    def __init__(self):
        self.api_key = "API Key here"
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def analyze_diff(self, diff_text: str) -> dict:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Review this git diff:\n\n{diff_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except Exception as e:
            return {
                "summary": "AI Review failed during processing.",
                "comments": [],
                "error": str(e)
            }