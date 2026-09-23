import json
from google import genai
from google.genai import types

SYSTEM_PROMPT = """
You are a Staff Software Engineer performing an automated Code Review on a Git Diff.
Your goal is to evaluate code changes and deliver concise, high-value suggestions.

Focus on:
1. Critical bugs, memory leaks, or race conditions
2. Security issues or hardcoded secrets
3. Performance bottlenecks or anti-patterns
4. Code clarity and dead code removal

VERDICT RULES:
- "APPROVE": Clean code, no bugs/issues, completely safe to merge.
- "REQUEST_CHANGES": Critical bugs, security flaws, or major anti-patterns found.
- "COMMENT": Minor non-blocking suggestions or technical feedback.

You MUST reply ONLY with a JSON object strictly following this format:
{
  "verdict": "APPROVE",
  "summary": "Short 2-3 sentence overview of the pull request changes.",
  "suggestions": [
    {
      "file": "path/to/file.swift",
      "line_info": "Line 38" (or "General"),
      "title": "Clear action-oriented title",
      "recommendation": "Detailed description of what should be changed and why."
    }
  ]
}
"""


class AIReviewer:
    def __init__(self):
        self.api_key = "Type your Gemini API Key here"  # Gemini API Key
        self.client = genai.Client(api_key=self.api_key)

    async def analyze_diff(self, diff_text: str) -> dict:
        """Step 2: Send code diff to Gemini API for review and verdict."""
        try:
            response = await self.client.aio.models.generate_content(
               # model="gemini-3.6-flash",
                model="gemini-3.8-flash",
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
                "verdict": "COMMENT",
                "summary": "AI Review failed during processing.",
                "suggestions": [],
                "error": str(e)
            }