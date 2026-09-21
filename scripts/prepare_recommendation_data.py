from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCE = DATA_DIR / "indian-job-market-dataset-2025.xlsx"
OUTPUT = DATA_DIR / "recommendation_jobs.csv"

if not SOURCE.exists():
    raise FileNotFoundError(f"Missing: {SOURCE}")

df = pd.read_excel(SOURCE)

required = [
    "title", "jobId", "companyName", "tagsAndSkills",
    "experience", "salary", "location", "jobDescription",
    "minimumSalary", "maximumSalary",
    "minimumExperience", "maximumExperience"
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

df.to_csv(OUTPUT, index=False)

print(f"Saved {len(df):,} jobs to {OUTPUT}")
