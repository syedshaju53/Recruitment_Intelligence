import pandas as pd


def create_demand_target(df):

    data = df.copy()

    # Remove records without essential fields
    data = data.dropna(
        subset=["title", "company_name", "location"]
    ).copy()

    # Calculate role-level posting volume
    role_counts = (
        data["title"]
        .value_counts()
        .rename("role_posting_count")
    )

    data = data.join(
        role_counts,
        on="title"
    )

    # Calculate company-level posting volume
    company_counts = (
        data["company_name"]
        .value_counts()
        .rename("company_posting_count")
    )

    data = data.join(
        company_counts,
        on="company_name"
    )

    # Calculate location-level posting volume
    location_counts = (
        data["location"]
        .value_counts()
        .rename("location_posting_count")
    )

    data = data.join(
        location_counts,
        on="location"
    )

    # Create demand score from observable market activity
    data["demand_score"] = (
        data["role_posting_count"] * 0.50
        + data["company_posting_count"] * 0.30
        + data["location_posting_count"] * 0.20
    )

    # Define threshold using the median
    threshold = data["demand_score"].median()

    data["demand_class"] = (
        data["demand_score"] >= threshold
    ).astype(int)

    return data


if __name__ == "__main__":

    from modules.job_market_analysis import load_job_market_data

    df = load_job_market_data()

    ml_data = create_demand_target(df)

    print("\n===== ML TARGET DATASET =====")

    print(
        ml_data[
            [
                "title",
                "company_name",
                "location",
                "role_posting_count",
                "company_posting_count",
                "location_posting_count",
                "demand_score",
                "demand_class"
            ]
        ].head(20).to_string(index=False)
    )

    print("\n===== DEMAND CLASS DISTRIBUTION =====")

    print(
        ml_data["demand_class"]
        .value_counts()
        .sort_index()
    )

    print("\n===== DEMAND THRESHOLD =====")

    print(
        ml_data["demand_score"].median()
    )