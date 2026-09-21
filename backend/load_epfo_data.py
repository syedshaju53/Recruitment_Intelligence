from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.epfo import EPFONationalPayroll


EPFO_DATA = [
    {
        "period": "2017-18",
        "age_group": "All",
        "member_count": 1552940,
        "establishments": 38363
    },
    {
        "period": "2018-19",
        "age_group": "All",
        "member_count": 6112223,
        "establishments": 60884
    },
    {
        "period": "2019-20",
        "age_group": "All",
        "member_count": 7858394,
        "establishments": 52738
    },
    {
        "period": "2020-21",
        "age_group": "All",
        "member_count": 7708375,
        "establishments": 46656
    },
    {
        "period": "2021-22",
        "age_group": "All",
        "member_count": 12234625,
        "establishments": 62535
    },
    {
        "period": "2022-23",
        "age_group": "All",
        "member_count": 13851689,
        "establishments": 55337
    }
]


def load_epfo():

    db: Session = SessionLocal()

    try:
        db.query(EPFONationalPayroll).delete()

        for item in EPFO_DATA:
            record = EPFONationalPayroll(**item)
            db.add(record)

        db.commit()

        print(f"Loaded {len(EPFO_DATA)} EPFO national records.")

    except Exception as e:
        db.rollback()
        print("ERROR:", e)

    finally:
        db.close()


if __name__ == "__main__":
    load_epfo()