import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

@dataclass(frozen=True)
class Settings:
    # Rubric Weights (Baseline: 100 Points)
    WEIGHT_AI_DEPTH: int = 40
    WEIGHT_PYTHON_BACKEND: int = 30
    WEIGHT_CLOUD_FULLSTACK: int = 15
    WEIGHT_GITHUB: int = 10
    WEIGHT_ENGINEERING_DEPTH: int = 5

    # Penalties
    PENALTY_THIN_WRAPPER_DEFAULT: int = 10
    PENALTY_THIN_WRAPPER_MIN: int = 5
    PENALTY_THIN_WRAPPER_MAX: int = 15
    PENALTY_TUTORIAL_PROJECT: int = 5

    # GitHub Scoring Caps
    GITHUB_MAX_ACTIVITY_SCORE: int = 5
    GITHUB_MAX_REPO_SCORE: int = 5

    # Timeouts & Limits
    GITHUB_TIMEOUT_SECONDS: float = 3.0
    LLM_TIMEOUT_SECONDS: float = 12.0

    # API Keys & Model Config
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

settings = Settings()
