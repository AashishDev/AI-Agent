import json
from google import genai
from google.genai import types

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
        self.api_key = "AQ.Ab8RN6L4ldriAIcB0owmAm1Xg51CWRNgPVMFbJAcgovYLP4BfQ"
        self.client = genai.Client(api_key=self.api_key)

    async def analyze_diff(self, diff_text: str) -> dict:
        """Step 2: Generate review suggestions using Gemini API."""
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"Review this git diff:\n\n{diff_text}",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            return json.loads(response.text)
        except Exception as e:
            return {
                "summary": "AI Review failed during processing.",
                "comments": [],
                "error": str(e)
            }