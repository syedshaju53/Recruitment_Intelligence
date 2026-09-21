import pandas as pd

from modules.job_market_analysis import load_job_market_data
from backend.ml_target import create_demand_target
from backend.feature_engineering import engineer_features


def prepare_ml_dataset():

    # Load original market data
    df = load_job_market_data()

    # Create target
    data = create_demand_target(df)

    # Create engineered features
    data = engineer_features(data)

    # Features used by the ML model
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
        "company_name_length"
    ]

    target_column = "demand_class"

    ml_data = data[
        feature_columns + [target_column]
    ].copy()

    # Replace invalid salary zero values with NaN
    salary_columns = [
        "salary_midpoint",
        "salary_range"
    ]

    for column in salary_columns:
        ml_data[column] = ml_data[column].replace(
            0,
            pd.NA
        )

    # Display dataset information
    print("\n===== ML DATASET SHAPE =====")
    print(ml_data.shape)

    print("\n===== ML FEATURES =====")
    print(feature_columns)

    print("\n===== TARGET =====")
    print(target_column)

    print("\n===== MISSING VALUES =====")
    print(ml_data.isna().sum())

    print("\n===== TARGET DISTRIBUTION =====")
    print(
        ml_data[target_column]
        .value_counts()
        .sort_index()
    )

    print("\n===== SAMPLE ML DATA =====")
    print(
        ml_data.head(10)
        .to_string(index=False)
    )

    return ml_data


if __name__ == "__main__":

    prepare_ml_dataset()