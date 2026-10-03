from fastapi import FastAPI, HTTPException,Request
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
    Executes V1 workflow:
    1. Fetch PR details and raw diff from GitHub Public API
    2. Request review verdict and suggestions from Gemini AI
    3. Post well-formatted Markdown review comment back to the GitHub PR
    """
    try:
        # STEP 1: Fetch PR Details and Code Diff
        pr_info = await github_client_instance.get_pull_request(owner, repo, pr_number)
        raw_diff = await github_client_instance.get_pr_diff(owner, repo, pr_number)

        if not raw_diff.strip():
            return {"message": "PR diff is empty, skipping AI review."}

        sanitized_diff = github_client_instance.sanitize_diff(raw_diff)

        # STEP 2: Send Diff to Gemini AI for Review
        review_result = await ai_reviewer_instance.analyze_diff(sanitized_diff)

        verdict = review_result.get("verdict", "COMMENT").upper()
        summary = review_result.get("summary", "No summary provided.")
        suggestions = review_result.get("suggestions", [])

        # Configure status badge and message based on verdict
        if verdict == "APPROVE":
            status_badge = "### ✅ **Verdict: APPROVED (Ready to Merge)**"
            action_note = "Code looks clean and safe to merge! No blocking issues found."
        elif verdict == "REQUEST_CHANGES":
            status_badge = "### ❌ **Verdict: CHANGES REQUESTED**"
            action_note = "Please review and address the highlighted action items before merging."
        else:
            status_badge = "### 💬 **Verdict: COMMENT / NEUTRAL**"
            action_note = "Review completed with optional suggestions or guidance."

        # STEP 3: Build high-quality Markdown template for GitHub display
        comment_markdown = f"""## ♊ Reviewed by Gemini AI

> 🤖 *Automated Code Review*

{status_badge}
**Next Steps:** {action_note}

---

### 📝 **Summary**
{summary}
"""

        # Format suggestions as clean Markdown callouts
        if suggestions:
            comment_markdown += "\n### 💡 **Suggested Improvements**\n\n"
            for idx, item in enumerate(suggestions, 1):
                file_path = item.get("file", "General")
                line_info = item.get("line_info", "N/A")
                title = item.get("title", "Suggestion")
                recommendation = item.get("recommendation", "")

                comment_markdown += f"#### {idx}. {title}\n"
                comment_markdown += f"- **File:** `{file_path}` ({line_info})\n"
                comment_markdown += f"- **Recommendation:** {recommendation}\n\n"
        else:
            comment_markdown += "\n---\n*✨ No code suggestions or warnings identified in this diff.*\n"

        if review_result.get("error"):
            comment_markdown += f"\n\n> ⚠️ **System Warning:** `{review_result['error']}`"

        comment_markdown += "\n\n---\n*Powered by FastAPI & Google Gemini API*"

        # Post comment back to GitHub
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


    # GitHub Web hook Integration (Optional)

@app.post("/github/webhook")
async def github_webhook(request: Request):
    """
    GitHub webhook endpoint.

    Triggered when a Pull Request is:
    - opened
    - updated with new commits (synchronize)
    """

    try:
        payload = await request.json()

        action = payload.get("action")

        # We only review newly opened PRs and updated PRs
        if action not in ["opened", "synchronize"]:
            return {
                "status": "ignored",
                "reason": f"Action '{action}' is not handled"
            }

        pull_request = payload.get("pull_request")

        if not pull_request:
            raise HTTPException(
                status_code=400,
                detail="Pull request information missing"
            )

        # PR number
        pr_number = pull_request.get("number")

        # Repository information
        repository = payload.get("repository", {})

        repo_name = repository.get("name")

        # Repository owner
        owner = repository.get("owner", {}).get("login")

        if not owner or not repo_name or not pr_number:
            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub webhook payload"
            )

        print(
            f"🔔 GitHub Webhook received: "
            f"{owner}/{repo_name} PR #{pr_number} "
            f"Action={action}"
        )

        # Trigger your existing PR review workflow
        result = await run_full_pr_review(
            owner=owner,
            repo=repo_name,
            pr_number=pr_number
        )

        return {
            "status": "success",
            "action": action,
            "owner": owner,
            "repo": repo_name,
            "pr_number": pr_number,
            "review_result": result
        }

    except HTTPException:
        raise

    except Exception as e:
        print(
            f"❌ WEBHOOK ERROR: "
            f"{type(e).__name__} - {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )