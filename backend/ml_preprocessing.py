import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def prepare_training_data(ml_data):

    data = ml_data.copy()

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

    X = data[feature_columns].copy()
    y = data["demand_class"].copy()

    # Convert every feature to numeric.
    # Invalid values and pandas NA become NumPy-compatible NaN.
    for column in feature_columns:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce"
        )

    # Missing-value indicators
    X["salary_missing"] = (
        X["salary_midpoint"].isna()
    ).astype(int)

    X["experience_missing"] = (
        X["minimum_experience"].isna()
    ).astype(int)

    # Train/Test split FIRST
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # Fit imputer ONLY on training data
    imputer = SimpleImputer(
        strategy="median"
    )

    X_train_imputed = imputer.fit_transform(
        X_train
    )

    X_test_imputed = imputer.transform(
        X_test
    )

    # Convert arrays back to DataFrames
    X_train_imputed = pd.DataFrame(
        X_train_imputed,
        columns=X.columns,
        index=X_train.index
    )

    X_test_imputed = pd.DataFrame(
        X_test_imputed,
        columns=X.columns,
        index=X_test.index
    )

    # Fit scaler ONLY on training data
    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train_imputed
    )

    X_test_scaled = scaler.transform(
        X_test_imputed
    )

    X_train_scaled = pd.DataFrame(
        X_train_scaled,
        columns=X.columns,
        index=X_train.index
    )

    X_test_scaled = pd.DataFrame(
        X_test_scaled,
        columns=X.columns,
        index=X_test.index
    )

    return (
        X_train_scaled,
        X_test_scaled,
        y_train,
        y_test,
        imputer,
        scaler
    )


if __name__ == "__main__":

    from backend.prepare_ml_dataset import (
        prepare_ml_dataset
    )

    ml_data = prepare_ml_dataset()

    (
        X_train,
        X_test,
        y_train,
        y_test,
        imputer,
        scaler
    ) = prepare_training_data(
        ml_data
    )

    print("\n===== TRAINING DATA =====")
    print("X_train:", X_train.shape)
    print("y_train:", y_train.shape)

    print("\n===== TEST DATA =====")
    print("X_test:", X_test.shape)
    print("y_test:", y_test.shape)

    print("\n===== TRAINING CLASS DISTRIBUTION =====")
    print(
        y_train
        .value_counts()
        .sort_index()
    )

    print("\n===== TEST CLASS DISTRIBUTION =====")
    print(
        y_test
        .value_counts()
        .sort_index()
    )

    print("\n===== MISSING VALUES AFTER IMPUTATION =====")
    print(
        X_train.isna().sum()
    )

    print("\n===== FEATURE COLUMNS =====")
    print(
        X_train.columns.tolist()
    )