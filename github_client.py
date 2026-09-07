import logging
import datetime
import requests
from typing import Optional, Dict
from config import settings
from models import GitHubResult

logger = logging.getLogger(__name__)

# In-run memory cache to avoid redundant API calls for duplicate usernames
_GITHUB_CACHE: Dict[str, GitHubResult] = {}

def get_github_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Resume-Screening-System/1.0"
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
    return headers

def enrich_github_profile(username: Optional[str]) -> GitHubResult:
    """
    Lightweight public GitHub API enrichment.
    Queries user profile and recent repositories.
    Guarantees:
      - Never raises unhandled exceptions.
      - Never affects candidate eligibility.
      - Gracefully handles 403 (rate limit), 404 (not found), and network timeouts.
    """
    if not username:
        return GitHubResult(
            username=None,
            status="skipped",
            summary="No GitHub profile found on resume"
        )

    clean_username = username.strip().lower()
    if clean_username in _GITHUB_CACHE:
        return _GITHUB_CACHE[clean_username]

    headers = get_github_headers()
    timeout = settings.GITHUB_TIMEOUT_SECONDS

    try:
        # 1. Fetch user profile
        user_url = f"https://api.github.com/users/{clean_username}"
        user_resp = requests.get(user_url, headers=headers, timeout=timeout)

        if user_resp.status_code == 404:
            res = GitHubResult(
                username=username,
                status="not_found",
                summary="GitHub profile not found"
            )
            _GITHUB_CACHE[clean_username] = res
            return res

        if user_resp.status_code == 403:
            logger.info(f"GitHub API rate limited for user {username}")
            res = GitHubResult(
                username=username,
                status="rate_limited",
                summary="GitHub enrichment skipped due to API rate limit"
            )
            _GITHUB_CACHE[clean_username] = res
            return res

        if user_resp.status_code != 200:
            res = GitHubResult(
                username=username,
                status="error",
                summary=f"GitHub API returned HTTP {user_resp.status_code}"
            )
            _GITHUB_CACHE[clean_username] = res
            return res

        user_data = user_resp.json()
        public_repos = user_data.get("public_repos", 0)
        updated_at_str = user_data.get("updated_at")

        # 2. Estimate activity score (0–5)
        activity_score = 0
        if updated_at_str:
            try:
                # updated_at format: 2026-03-01T12:00:00Z
                updated_at = datetime.datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                now = datetime.datetime.now(datetime.timezone.utc)
                days_since_update = (now - updated_at).days

                if days_since_update <= 30:
                    activity_score = 5
                elif days_since_update <= 90:
                    activity_score = 3
                elif days_since_update <= 180:
                    activity_score = 2
                else:
                    activity_score = 1
            except Exception:
                activity_score = 1 if public_repos > 0 else 0

        # 3. Fetch recent repos to estimate maintained / relevant repos score (0–5)
        repos_url = f"https://api.github.com/users/{clean_username}/repos?per_page=10&sort=updated"
        repos_resp = requests.get(repos_url, headers=headers, timeout=timeout)
        
        repo_score = 0
        relevant_repo_count = 0
        if repos_resp.status_code == 200:
            repos_data = repos_resp.json()
            if isinstance(repos_data, list):
                for repo in repos_data:
                    # Ignore forks
                    if repo.get("fork"):
                        continue
                    lang = (repo.get("language") or "").lower()
                    desc = (repo.get("description") or "").lower()
                    name = (repo.get("name") or "").lower()
                    topics = [t.lower() for t in repo.get("topics", [])]
                    
                    # Check for Python or AI signals
                    is_python = "python" in lang or "python" in desc or "python" in name
                    is_ai = any(kw in desc or kw in name or kw in topics for kw in ["rag", "llm", "agent", "langchain", "ai", "model", "fastapi"])
                    
                    if is_python or is_ai:
                        relevant_repo_count += 1

                if relevant_repo_count >= 3:
                    repo_score = 5
                elif relevant_repo_count >= 1:
                    repo_score = 3
                elif public_repos > 0:
                    repo_score = 1
        elif repos_resp.status_code == 403:
            logger.info("GitHub repos call rate limited; using profile signals")
            repo_score = 2 if public_repos > 2 else 1

        total_score = min(settings.WEIGHT_GITHUB, activity_score + repo_score)
        summary = f"Active profile ({activity_score}/5 activity); {relevant_repo_count} relevant/maintained Python/AI repo(s) ({repo_score}/5 repos)."

        result = GitHubResult(
            username=username,
            activity_score=activity_score,
            repo_score=repo_score,
            total_score=total_score,
            status="success",
            summary=summary
        )
        _GITHUB_CACHE[clean_username] = result
        return result

    except Exception as e:
        logger.warning(f"GitHub enrichment error for {username}: {e}")
        res = GitHubResult(
            username=username,
            status="error",
            summary="GitHub enrichment skipped due to network error"
        )
        _GITHUB_CACHE[clean_username] = res
        return res
