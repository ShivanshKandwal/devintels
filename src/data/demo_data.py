"""
Synthetic Demo Data Generator.

Produces a realistic 5 000-row DataFrame matching the Stack Overflow Developer
Survey schema so the full DevIntel pipeline can run without real data.

Usage:
    python -m src.data.demo_data          # writes to data/raw/demo_survey_2024.csv
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_ROWS = 5_000

# ── realistic value pools ─────────────────────────────────────────────────

MAIN_BRANCH = [
    "I am a developer by profession",
    "I am not primarily a developer, but I write code sometimes as part of my work",
    "I code primarily as a hobby",
    "I am a student who is learning to code",
    "I used to be a developer by profession, but no longer am",
]
MAIN_BRANCH_W = [0.55, 0.15, 0.12, 0.12, 0.06]

EMPLOYMENT = [
    "Employed, full-time",
    "Employed, part-time",
    "Independent contractor, freelancer, or self-employed",
    "Not employed, but looking for work",
    "Student, full-time",
    "Student, part-time",
    "Not employed, and not looking for work",
    "Retired",
]
EMPLOYMENT_W = [0.52, 0.07, 0.12, 0.08, 0.10, 0.04, 0.05, 0.02]

REMOTE_WORK = ["Remote", "Hybrid (some remote, some in-person)", "In-person"]
REMOTE_WORK_W = [0.38, 0.35, 0.27]

ED_LEVELS = [
    "Bachelor's degree (B.A., B.S., B.Eng., etc.)",
    "Master's degree (M.A., M.S., M.Eng., MBA, etc.)",
    "Some college/university study without earning a degree",
    "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)",
    "Associate degree (A.A., A.S., etc.)",
    "Professional degree (JD, MD, Ph.D, Ed.D, etc.)",
    "Primary/elementary school",
    "Something else",
]
ED_LEVELS_W = [0.35, 0.25, 0.13, 0.10, 0.06, 0.06, 0.02, 0.03]

DEV_TYPES = [
    "Developer, full-stack",
    "Developer, back-end",
    "Developer, front-end",
    "Developer, desktop or enterprise applications",
    "Developer, mobile",
    "DevOps specialist",
    "Database administrator",
    "System administrator",
    "Data scientist or machine learning specialist",
    "Data or business analyst",
    "Academic researcher",
    "Engineer, data",
    "Developer, embedded applications or devices",
    "Developer, QA or test",
    "Engineering manager",
    "Cloud infrastructure engineer",
    "Security professional",
    "Designer",
    "Product manager",
    "Educator",
    "Developer, game or graphics",
    "Scientist",
    "Developer Advocate",
    "Blockchain",
]

ORG_SIZES = [
    "Just me - I am a freelancer, sole proprietor, etc.",
    "2 to 9 employees",
    "10 to 19 employees",
    "20 to 99 employees",
    "100 to 499 employees",
    "500 to 999 employees",
    "1,000 to 4,999 employees",
    "5,000 to 9,999 employees",
    "10,000 or more employees",
    "I don't know",
]
ORG_SIZES_W = [0.08, 0.10, 0.07, 0.12, 0.14, 0.08, 0.13, 0.08, 0.15, 0.05]

COUNTRIES = [
    "United States of America", "India", "Germany", "United Kingdom of Great Britain and Northern Ireland",
    "Canada", "France", "Brazil", "Netherlands", "Poland", "Australia",
    "Spain", "Italy", "Sweden", "Israel", "Switzerland", "Turkey",
    "Russian Federation", "Nigeria", "Japan", "Mexico",
    "Argentina", "South Africa", "Indonesia", "Pakistan",
    "Ukraine", "China", "South Korea", "Philippines",
]
COUNTRIES_W = [
    0.18, 0.14, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03,
    0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.01, 0.02,
    0.01, 0.01, 0.02, 0.02, 0.01, 0.03, 0.01, 0.02,
]

LANGUAGES = [
    "JavaScript", "HTML/CSS", "Python", "SQL", "TypeScript", "Bash/Shell",
    "Java", "C#", "C++", "C", "PHP", "Go", "Rust", "Kotlin",
    "Ruby", "Lua", "Dart", "Swift", "R", "MATLAB", "Scala",
    "Perl", "Haskell", "Elixir", "Clojure", "Assembly", "VBA",
]
LANG_WEIGHTS = [
    0.65, 0.55, 0.50, 0.48, 0.38, 0.30,
    0.30, 0.27, 0.22, 0.18, 0.18, 0.14, 0.13, 0.10,
    0.06, 0.05, 0.06, 0.05, 0.05, 0.04, 0.03,
    0.03, 0.02, 0.03, 0.02, 0.03, 0.04,
]

DATABASES = [
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Microsoft SQL Server",
    "Redis", "MariaDB", "Elasticsearch", "DynamoDB", "Oracle",
    "Firebase Realtime Database", "Cloud Firestore", "Cosmos DB",
    "Cassandra", "Neo4j", "CouchDB", "Couchbase",
]
DB_WEIGHTS = [
    0.45, 0.41, 0.32, 0.26, 0.26,
    0.22, 0.17, 0.13, 0.11, 0.11,
    0.10, 0.08, 0.07,
    0.04, 0.04, 0.03, 0.02,
]

PLATFORMS = [
    "Amazon Web Services (AWS)", "Microsoft Azure", "Google Cloud",
    "Cloudflare", "Digital Ocean", "Heroku", "Vercel", "Netlify",
    "Firebase", "VMware", "Hetzner", "OVH", "Linode, now Akamai",
]

MISC_TECH = [
    "Docker", "npm", "Homebrew", "Pip", "Yarn", "Webpack", "Make",
    "Kubernetes", "NuGet", "Gradle", "Terraform", "Ansible",
    "Pulumi", "Podman",
]

TOOLS_TECH = [
    "Visual Studio Code", "Visual Studio", "IntelliJ IDEA",
    "Notepad++", "Vim", "Android Studio", "PyCharm", "Sublime Text",
    "Eclipse", "Xcode", "Nano", "WebStorm", "PhpStorm", "Neovim",
    "Atom", "Rider", "DataGrip", "CLion", "IPython/Jupyter",
    "RStudio", "GoLand", "Emacs",
]

COLLAB_TOOLS = [
    "Jira", "Confluence", "GitHub Discussions", "Slack",
    "Microsoft Teams", "Trello", "Notion", "Asana",
    "Linear", "Azure Devops", "Mattermost", "Basecamp",
    "Stack Overflow for Teams", "Wikis",
]

AI_SEARCH = [
    "ChatGPT", "Bing AI", "Google Bard AI", "WolframAlpha",
    "Phind", "You.com", "Perplexity AI",
]

AI_DEV = [
    "GitHub Copilot", "Tabnine", "AWS CodeWhisperer",
    "Codeium", "Replit Ghostwriter", "Whispr AI",
    "Visual Studio IntelliCode",
]

LEARN_CODE = [
    "Other online resources (e.g., videos, blogs, forum)",
    "School (i.e., University, College, etc)",
    "Books / Physical media",
    "On the job training",
    "Online Courses or Certification",
    "Coding Bootcamp",
    "Friend or family member",
    "Hackathons (virtual or in-person)",
]

LEARN_ONLINE = [
    "Technical documentation", "Stack Overflow", "Blogs",
    "How-to videos", "Written Tutorials", "Online books",
    "Interactive tutorial", "Online challenges (e.g., daily coding challenge)",
    "Video-based Online Courses", "Auditing university courses",
]

LEARN_COURSES = [
    "Udemy", "Coursera", "Codecademy", "edX",
    "Pluralsight", "LinkedIn Learning", "Skillshare",
    "Udacity", "FreeCodeCamp",
]

JOB_SAT = [
    "Very satisfied",
    "Slightly satisfied",
    "Neither satisfied nor dissatisfied",
    "Slightly dissatisfied",
    "Very dissatisfied",
]
JOB_SAT_W = [0.28, 0.30, 0.18, 0.14, 0.10]

INDUSTRIES = [
    "Information Services, IT, Software Development, or other Technology",
    "Financial Services",
    "Manufacturing, Transportation, or Supply Chain",
    "Healthcare",
    "Retail and Consumer Services",
    "Higher Education",
    "Insurance",
    "Wholesale",
    "Oil & Gas",
    "Advertising Services",
    "Legal Services",
]
INDUSTRIES_W = [0.40, 0.12, 0.08, 0.07, 0.06, 0.06, 0.04, 0.04, 0.04, 0.05, 0.04]

CODING_ACTIVITIES = [
    "Hobby", "Professional development or self-paced learning",
    "Contribute to open-source projects", "Freelance/contract work",
    "Bootstrapping a business", "School or academic work", "I don't code outside of work",
]

AI_SELECT = ["Yes", "No, but I plan to soon", "No, and I don't plan to"]
AI_SELECT_W = [0.50, 0.25, 0.25]

AI_SENT = [
    "Very favorable", "Favorable", "Indifferent",
    "Unsure", "Unfavorable", "Very unfavorable",
]
AI_SENT_W = [0.18, 0.32, 0.22, 0.12, 0.10, 0.06]

SO_VISIT_FREQ = [
    "Multiple times per day", "Daily or almost daily",
    "A few times per week", "A few times per month or weekly",
    "Less than once per month or monthly", "I have never visited Stack Overflow",
]
SO_VISIT_FREQ_W = [0.20, 0.25, 0.25, 0.15, 0.10, 0.05]

ICORPM = ["Individual contributor", "People manager", "A mix of both"]
ICORPM_W = [0.60, 0.15, 0.25]

CURRENCIES = ["USD", "EUR", "GBP", "INR", "CAD", "AUD", "BRL", "JPY", "CHF", "PLN"]
CURRENCIES_W = [0.30, 0.18, 0.08, 0.14, 0.06, 0.04, 0.05, 0.03, 0.03, 0.09]


# ── helpers ───────────────────────────────────────────────────────────────


def _pick_multi(rng: np.random.Generator, pool: list[str], weights: list[float] | None = None,
                min_items: int = 1, max_items: int = 6) -> str:
    """Pick several items from *pool* and join with semicolons."""
    n = rng.integers(min_items, max_items + 1)
    n = min(n, len(pool))
    if weights is not None:
        w = np.array(weights, dtype=float)
        w /= w.sum()
        chosen = rng.choice(pool, size=n, replace=False, p=w)
    else:
        chosen = rng.choice(pool, size=n, replace=False)
    return ";".join(chosen)


def _salary_for_country(rng: np.random.Generator, country: str) -> float:
    """Generate a realistic salary in USD for a given country."""
    medians: dict[str, tuple[float, float]] = {
        "United States of America": (95_000, 45_000),
        "United Kingdom of Great Britain and Northern Ireland": (65_000, 25_000),
        "Germany": (70_000, 25_000),
        "Canada": (72_000, 28_000),
        "Australia": (78_000, 30_000),
        "Switzerland": (110_000, 35_000),
        "India": (14_000, 10_000),
        "Brazil": (18_000, 12_000),
        "Nigeria": (8_000, 6_000),
        "Poland": (30_000, 15_000),
        "France": (52_000, 20_000),
    }
    median, std = medians.get(country, (35_000, 20_000))
    salary = rng.normal(median, std)
    return float(max(salary, 1_200))


YEARS_CODE_VALS = [
    "Less than 1 year", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "20", "25", "30", "35", "40", "More than 50 years",
]

WORK_EXP_VALS = list(range(0, 46))


# ── main generator ────────────────────────────────────────────────────────


def generate_demo_data(
    n_rows: int = DEFAULT_ROWS,
    seed: int = 42,
    survey_year: int = 2024,
) -> pd.DataFrame:
    """Generate *n_rows* of synthetic survey data.

    Parameters
    ----------
    n_rows:
        Number of rows to generate.
    seed:
        Random seed for reproducibility.
    survey_year:
        Value to stamp into a ``survey_year`` column.

    Returns
    -------
    pd.DataFrame with columns matching the Stack Overflow survey schema.
    """
    rng = np.random.default_rng(seed)
    records: list[dict[str, Any]] = []

    for i in range(1, n_rows + 1):
        country = rng.choice(COUNTRIES, p=COUNTRIES_W)
        employment = rng.choice(EMPLOYMENT, p=EMPLOYMENT_W)
        is_employed = employment.startswith("Employed") or "contractor" in employment.lower()

        yrs_code_idx = min(int(rng.exponential(6)), len(YEARS_CODE_VALS) - 1)
        yrs_code = YEARS_CODE_VALS[yrs_code_idx]

        yrs_pro_idx = max(0, yrs_code_idx - rng.integers(0, 4))
        yrs_pro = YEARS_CODE_VALS[min(yrs_pro_idx, len(YEARS_CODE_VALS) - 1)]

        n_dev_types = rng.integers(1, 5)
        dev_type = ";".join(rng.choice(DEV_TYPES, size=min(n_dev_types, len(DEV_TYPES)), replace=False))

        salary = _salary_for_country(rng, country) if is_employed and rng.random() > 0.2 else np.nan
        work_exp = int(rng.integers(0, 41)) if is_employed else (int(rng.integers(0, 10)) if rng.random() > 0.5 else np.nan)

        record: dict[str, Any] = {
            "ResponseId": i + survey_year * 100_000,
            "MainBranch": rng.choice(MAIN_BRANCH, p=MAIN_BRANCH_W),
            "Employment": employment,
            "RemoteWork": rng.choice(REMOTE_WORK, p=REMOTE_WORK_W) if is_employed else np.nan,
            "CodingActivities": _pick_multi(rng, CODING_ACTIVITIES, max_items=4),
            "EdLevel": rng.choice(ED_LEVELS, p=ED_LEVELS_W),
            "YearsCode": yrs_code,
            "YearsCodePro": yrs_pro if is_employed else np.nan,
            "DevType": dev_type,
            "OrgSize": rng.choice(ORG_SIZES, p=ORG_SIZES_W) if is_employed else np.nan,
            "Country": country,
            "Currency": rng.choice(CURRENCIES, p=CURRENCIES_W),
            "ConvertedCompYearly": salary,
            "JobSat": rng.choice(JOB_SAT, p=JOB_SAT_W) if is_employed else np.nan,
            "Industry": rng.choice(INDUSTRIES, p=INDUSTRIES_W) if is_employed else np.nan,
            "LanguageHaveWorkedWith": _pick_multi(rng, LANGUAGES, LANG_WEIGHTS, min_items=2, max_items=8),
            "LanguageWantToWorkWith": _pick_multi(rng, LANGUAGES, LANG_WEIGHTS, min_items=1, max_items=5),
            "DatabaseHaveWorkedWith": _pick_multi(rng, DATABASES, DB_WEIGHTS, min_items=1, max_items=5),
            "DatabaseWantToWorkWith": _pick_multi(rng, DATABASES, DB_WEIGHTS, min_items=0, max_items=4),
            "PlatformHaveWorkedWith": _pick_multi(rng, PLATFORMS, min_items=0, max_items=4),
            "MiscTechHaveWorkedWith": _pick_multi(rng, MISC_TECH, min_items=1, max_items=5),
            "ToolsTechHaveWorkedWith": _pick_multi(rng, TOOLS_TECH, min_items=1, max_items=4),
            "NEWCollabToolsHaveWorkedWith": _pick_multi(rng, COLLAB_TOOLS, min_items=1, max_items=5),
            "AISearchHaveWorkedWith": _pick_multi(rng, AI_SEARCH, min_items=0, max_items=4) if rng.random() > 0.25 else np.nan,
            "AIDevHaveWorkedWith": _pick_multi(rng, AI_DEV, min_items=0, max_items=3) if rng.random() > 0.35 else np.nan,
            "LearnCode": _pick_multi(rng, LEARN_CODE, min_items=1, max_items=4),
            "LearnCodeOnline": _pick_multi(rng, LEARN_ONLINE, min_items=1, max_items=5),
            "LearnCodeCoursesCert": _pick_multi(rng, LEARN_COURSES, min_items=0, max_items=3) if rng.random() > 0.3 else np.nan,
            "WorkExp": work_exp,
            "ICorPM": rng.choice(ICORPM, p=ICORPM_W) if is_employed else np.nan,
            "SOVisitFreq": rng.choice(SO_VISIT_FREQ, p=SO_VISIT_FREQ_W),
            "SOAccount": rng.choice(["Yes", "No"], p=[0.65, 0.35]),
            "SOPartFreq": rng.choice(
                ["A few times per month or weekly", "Less than once per month or monthly",
                 "A few times per week", "Daily or almost daily", "I have never participated in Q&A on Stack Overflow"],
                p=[0.25, 0.25, 0.15, 0.05, 0.30],
            ),
            "AISelect": rng.choice(AI_SELECT, p=AI_SELECT_W),
            "AISent": rng.choice(AI_SENT, p=AI_SENT_W),
            "AIToolCurrentlyUsing": _pick_multi(rng, AI_DEV + AI_SEARCH, min_items=0, max_items=4) if rng.random() > 0.35 else np.nan,
            "AIToolInterested": _pick_multi(rng, AI_DEV + AI_SEARCH, min_items=0, max_items=3) if rng.random() > 0.40 else np.nan,
            "survey_year": survey_year,
        }
        records.append(record)

    df = pd.DataFrame(records)
    logger.info("Generated %d synthetic rows for survey_year=%d", len(df), survey_year)
    return df


# ── multi-year generation ─────────────────────────────────────────────────


def generate_multi_year(
    years: tuple[int, ...] = (2022, 2023, 2024),
    rows_per_year: int = DEFAULT_ROWS,
    seed: int = 42,
    output_dir: Path | None = None,
) -> list[Path]:
    """Generate one CSV per year and write to *output_dir*.

    Returns list of written file paths.
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for idx, year in enumerate(years):
        df = generate_demo_data(n_rows=rows_per_year, seed=seed + idx, survey_year=year)
        path = output_dir / f"demo_survey_{year}.csv"
        df.to_csv(path, index=False)
        logger.info("Wrote %s (%d rows)", path, len(df))
        paths.append(path)

    return paths


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    paths = generate_multi_year()
    print(f"\n✅  Generated {len(paths)} demo CSVs:")
    for p in paths:
        print(f"   📄 {p}")


if __name__ == "__main__":
    main()
