import httpx


class GitHubClient:
    BASE_URL = "https://api.github.com"
    TOKEN = "Type your GitHub Personal Access Token here"  # Must have 'repo' scope permissions

    def _get_headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.TOKEN:
            headers["Authorization"] = f"Bearer {self.TOKEN}"
        return headers

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> dict:
        """Step 1a: Fetch Pull Request details from GitHub."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Step 1b: Fetch raw Unified Code Diff from GitHub."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers()
        headers["Accept"] = "application/vnd.github.v3.diff"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"GitHub API returned {response.status_code}: {response.text}")

        return response.text

    def sanitize_diff(self, diff_text: str, max_chars: int = 50000) -> str:
        """Truncates diff to prevent LLM context window overflow."""
        if len(diff_text) > max_chars:
            return diff_text[:max_chars] + "\n\n...[Diff truncated due to size limits]..."
        return diff_text

    async def post_issue_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict:
        """Step 3: Post formatted AI review comment back to the GitHub PR."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json={"body": body}
            )

        if response.status_code not in (200, 201):
            raise Exception(f"Failed to post comment on GitHub: {response.status_code} - {response.text}")

        return response.json()