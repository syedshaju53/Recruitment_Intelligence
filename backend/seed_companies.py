import pandas as pd
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.company import Company


CSV_PATH = "data/companies.csv"


def seed_companies():
    print("Reading companies.csv...")

    df = pd.read_csv(CSV_PATH)

    print(f"Found {len(df)} companies.")
    print("Columns:", list(df.columns))

    required_columns = [
        "company_id",
        "company_name",
        "industry",
        "headquarters",
        "rating",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    db: Session = SessionLocal()

    try:
        inserted = 0
        skipped = 0

        for _, row in df.iterrows():

            existing_company = (
                db.query(Company)
                .filter(
                    Company.company_id == str(row["company_id"])
                )
                .first()
            )

            if existing_company:
                skipped += 1
                continue

            company = Company(
                company_id=str(row["company_id"]),
                company_name=str(row["company_name"]),
                rating=float(row["rating"])
            )

            db.add(company)
            inserted += 1

        db.commit()

        print("\nCOMPANY SEEDING COMPLETED")
        print(f"Inserted : {inserted}")
        print(f"Skipped  : {skipped}")

    except Exception as e:
        db.rollback()
        print("\nERROR DURING COMPANY SEEDING")
        print(e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_companies()