import httpx


class GitHubClient:

    BASE_URL = "https://api.github.com"
    TOKEN = "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"

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetches the raw Unified Diff of a Pull Request."""

        url = (
            f"{self.BASE_URL}/repos/"
            f"{owner}/{repo}/pulls/{pr_number}"
        )

        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if self.TOKEN:
            headers["Authorization"] = f"Bearer {self.TOKEN}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"GitHub API returned {response.status_code}: {response.text}"
            )

        return response.text


    def sanitize_diff(
            self, diff_text: str, max_chars: int = 50000) -> str:
        """
        Truncates diffs that are too large to fit safely into standard LLM context windows.
        """
        if len(diff_text) > max_chars:
            return diff_text[:max_chars] + "\n\n...[Diff truncated due to size limits]..."
        return diff_text


    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ):
        url = (
            f"{self.BASE_URL}/repos/"
            f"{owner}/{repo}/pulls/{pr_number}"
        )

        print("GitHub API URL:", url)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        print("GitHub Response Status:", response.status_code)

        response.raise_for_status()

        return response.json()