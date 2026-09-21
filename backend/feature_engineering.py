import pandas as pd


def engineer_features(df):

    data = df.copy()

    # Numeric conversions
    numeric_columns = [
        "minimum_experience",
        "maximum_experience",
        "minimum_salary",
        "maximum_salary",
        "aggregate_rating",
        "reviews_count"
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Salary midpoint
    data["salary_midpoint"] = (
        data["minimum_salary"] +
        data["maximum_salary"]
    ) / 2

    # Experience midpoint
    data["experience_midpoint"] = (
        data["minimum_experience"] +
        data["maximum_experience"]
    ) / 2

    # Salary range
    data["salary_range"] = (
        data["maximum_salary"] -
        data["minimum_salary"]
    )

    # Experience range
    data["experience_range"] = (
        data["maximum_experience"] -
        data["minimum_experience"]
    )

    # Number of skills
    data["skill_count"] = (
        data["tags_and_skills"]
        .fillna("")
        .astype(str)
        .apply(
            lambda x: len([
                skill.strip()
                for skill in x.replace("|", ",")
                .replace(";", ",")
                .split(",")
                if skill.strip()
            ])
        )
    )

    # Remote indicator
    data["is_remote"] = (
        data["location"]
        .fillna("")
        .astype(str)
        .str.contains(
            "remote",
            case=False,
            na=False
        )
        .astype(int)
    )

    # Job title length
    data["title_length"] = (
        data["title"]
        .fillna("")
        .astype(str)
        .str.len()
    )

    # Company name length
    data["company_name_length"] = (
        data["company_name"]
        .fillna("")
        .astype(str)
        .str.len()
    )

    return data

if __name__ == "__main__":

    from modules.job_market_analysis import load_job_market_data
    from backend.ml_target import create_demand_target

    df = load_job_market_data()

    data = create_demand_target(df)

    data = engineer_features(data)

    print("\n===== ENGINEERED FEATURES =====")

    feature_columns = [
        "minimum_experience",
        "maximum_experience",
        "salary_midpoint",
        "experience_midpoint",
        "salary_range",
        "experience_range",
        "skill_count",
        "is_remote",
        "title_length",
        "company_name_length",
        "demand_class"
    ]

    print(
        data[feature_columns]
        .head(20)
        .to_string(index=False)
    )

    print("\n===== FEATURE DATA TYPES =====")

    print(
        data[feature_columns].dtypes
    )

    print("\n===== MISSING VALUES =====")

    print(
        data[feature_columns]
        .isna()
        .sum()
    )