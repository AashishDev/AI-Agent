from fastapi import FastAPI, HTTPException
from app.github_client import GitHubClient
from app.ai_reviewer import AIReviewer

app = FastAPI(
    title="AI PR Review API",
    description="AI-Powered GitHub PR Reviewer Agent",
    version="1.0.0"
)

github_client_instance = GitHubClient()
ai_reviewer_instance = AIReviewer()


@app.get("/")
async def root():
    return {"message": "Welcome to the AI PR Reviewer"}


@app.post("/pr/{owner}/{repo}/{pr_number}/review")
async def run_full_pr_review(owner: str, repo: str, pr_number: int):
    """
    Executes complete 3-step workflow:
    1. Fetch PR details and raw diff from GitHub Public API
    2. Request code review suggestions from Gemini AI
    3. Post the AI suggestions back as a GitHub PR comment
    """
    try:
        # STEP 1: Fetch PR Details and Code Diff from GitHub API
        pr_info = await github_client_instance.get_pull_request(owner, repo, pr_number)
        raw_diff = await github_client_instance.get_pr_diff(owner, repo, pr_number)

        if not raw_diff.strip():
            return {"message": "PR diff is empty, skipping AI review."}

        sanitized_diff = github_client_instance.sanitize_diff(raw_diff)

        # STEP 2: Send Diff to Gemini AI for Review
        review_result = await ai_reviewer_instance.analyze_diff(sanitized_diff)

        # Format AI output into Markdown
        comment_markdown = f"## 🤖 AI Code Review Summary\n\n{review_result.get('summary', 'No summary provided.')}\n\n"

        inline_comments = review_result.get("comments", [])
        if inline_comments:
            comment_markdown += "### 💡 Suggested Changes & Notes:\n"
            for item in inline_comments:
                file_path = item.get("path", "General")
                line = item.get("line", "-")
                body = item.get("body", "")
                comment_markdown += f"- **`{file_path}`** (Line {line}): {body}\n"

        if review_result.get("error"):
            comment_markdown += f"\n⚠️ **Note:** {review_result['error']}"

        # STEP 3: Post AI Comments back to GitHub Repo
        posted_comment = await github_client_instance.post_issue_comment(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            body=comment_markdown
        )

        return {
            "status": "success",
            "pr_title": pr_info.get("title"),
            "github_comment_url": posted_comment.get("html_url"),
            "review": review_result
        }

    except Exception as e:
        print(f"❌ ERROR DURING PR REVIEW WORKFLOW: {type(e).__name__} - {str(e)}")
        status_code = 404 if "404" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))