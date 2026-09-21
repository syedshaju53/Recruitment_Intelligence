import pandas as pd
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.job_market_history import JobMarketHistory

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "data" / "indian-job-market-dataset-2025.xlsx"


def clean_value(value):
    if pd.isna(value):
        return None
    return value


def clean_float(value):
    if pd.isna(value):
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def load_data():

    df = pd.read_excel(FILE_PATH)

    df = df.rename(columns={
        "jobId": "job_id",
        "jobUploaded": "job_uploaded",
        "companyName": "company_name",
        "companyId": "company_id",
        "tagsAndSkills": "tags_and_skills",
        "ReviewsCount": "reviews_count",
        "AggregateRating": "aggregate_rating",
        "jobDescription": "job_description",
        "minimumSalary": "minimum_salary",
        "maximumSalary": "maximum_salary",
        "minimumExperience": "minimum_experience",
        "maximumExperience": "maximum_experience"
    })

    records = []

    for _, row in df.iterrows():

        record = JobMarketHistory(
            title=clean_value(row.get("title")),
            job_id=clean_value(row.get("job_id")),
            currency=clean_value(row.get("currency")),
            job_uploaded=clean_value(row.get("job_uploaded")),
            company_name=clean_value(row.get("company_name")),
            company_id=clean_value(row.get("company_id")),
            tags_and_skills=clean_value(row.get("tags_and_skills")),
            experience=clean_value(row.get("experience")),
            salary=clean_value(row.get("salary")),
            location=clean_value(row.get("location")),
            reviews_count=clean_float(row.get("reviews_count")),
            aggregate_rating=clean_float(row.get("aggregate_rating")),
            job_description=clean_value(row.get("job_description")),
            minimum_salary=clean_float(row.get("minimum_salary")),
            maximum_salary=clean_float(row.get("maximum_salary")),
            minimum_experience=clean_float(row.get("minimum_experience")),
            maximum_experience=clean_float(row.get("maximum_experience"))
        )

        records.append(record)

    db: Session = SessionLocal()

    try:

        db.query(JobMarketHistory).delete()

        db.bulk_save_objects(records)

        db.commit()

        print(f"Loaded {len(records)} job-market records successfully.")

    except Exception as e:

        db.rollback()
        print("ERROR:", e)

    finally:
        db.close()


if __name__ == "__main__":
    load_data()