from fastapi import FastAPI, HTTPException
from app import github_client
from app import ai_reviewer
from app.github_client import GitHubClient
from app.ai_reviewer import AIReviewer

app = FastAPI(
 title = "AI PR Review API",
 description = "AI-Powered Guthiub PR Reviewer agent",
 version = "1.0.0"
)

# Instantiate clients globally
github_client_instance = GitHubClient()
ai_reviewer_instance = AIReviewer()


@app.get("/")
async def root():
    return {"message": "Welcome to the AI PR Reviewer"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/pr/{owner}/{repo}/{pr_number}")
async def get_pull_request(owner: str, repo: str, pr_number: int):
    try:
        return await github_client_instance.get_pull_request(
            owner=owner, 
            repo=repo, 
            pr_number=pr_number
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pr/{owner}/{repo}/{pr_number}/diff")
async def get_pull_request_diff(owner: str, repo: str, pr_number: int):
    try:
        raw_diff = await github_client_instance.get_pr_diff(
            owner=owner, 
            repo=repo, 
            pr_number=pr_number
        )
        return {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "diff": raw_diff
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pr/{owner}/{repo}/{pr_number}/analyze")
async def analyze_pull_request(owner: str, repo: str, pr_number: int):
    """Fetch diff and process it through the AI Reviewer Engine."""
    try:
        # Step 1: Fetch PR diff using instantiated GitHub client
        diff_text = await github_client_instance.get_pr_diff(
            owner=owner,
            repo=repo, 
            pr_number=pr_number
        )
        
        # Step 2: Send diff to AI Reviewer using instantiated AI reviewer
        review_result = await ai_reviewer_instance.analyze_diff(diff_text)
        
        return {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "review": review_result
        }
    except Exception as e:
        print(f"❌ ERROR IN ANALYZE ENDPOINT: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))