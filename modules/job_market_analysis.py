import pandas as pd
from sqlalchemy import text
from scipy.stats import pearsonr

from backend.database import engine


def load_job_market_data():

    query = text("""
        SELECT
            title,
            company_name,
            tags_and_skills,
            experience,
            location,
            reviews_count,
            aggregate_rating,
            minimum_salary,
            maximum_salary,
            minimum_experience,
            maximum_experience
        FROM job_market_history
    """)

    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def company_analysis(df):

    company_df = df.dropna(subset=["company_name"]).copy()

    result = (
        company_df
        .groupby("company_name")
        .agg(
            job_postings=("title", "count"),
            average_rating=("aggregate_rating", "mean"),
            average_min_salary=("minimum_salary", "mean"),
            average_max_salary=("maximum_salary", "mean")
        )
        .sort_values(
            "job_postings",
            ascending=False
        )
    )

    return result

def role_analysis(df):

    role_df = df.dropna(subset=["title"]).copy()

    result = (
        role_df
        .groupby("title")
        .agg(
            job_postings=("title", "count"),
            companies=("company_name", "nunique"),
            locations=("location", "nunique")
        )
        .sort_values(
            "job_postings",
            ascending=False
        )
    )

    return result


def skill_analysis(df):

    skill_df = df.dropna(
        subset=["tags_and_skills"]
    ).copy()

    skills = (
        skill_df["tags_and_skills"]
        .astype(str)
        .str.replace("|", ",", regex=False)
        .str.replace(";", ",", regex=False)
        .str.split(",")
        .explode()
    )

    skills = (
        skills
        .str.strip()
        .str.lower()
    )

    skills = skills[
        (skills != "") &
        (skills != "nan")
    ]

    result = (
        skills
        .value_counts()
        .head(30)
        .reset_index()
    )

    result.columns = [
        "skill",
        "job_postings"
    ]

    return result

def location_analysis(df):

    location_df = df.dropna(
        subset=["location"]
    ).copy()

    result = (
        location_df
        .groupby("location")
        .agg(
            job_postings=("title", "count"),
            companies=("company_name", "nunique"),
            roles=("title", "nunique")
        )
        .sort_values(
            "job_postings",
            ascending=False
        )
    )

    return result

def experience_salary_analysis(df):

    analysis_df = df.copy()

    # Convert numeric columns safely
    numeric_columns = [
        "minimum_experience",
        "maximum_experience",
        "minimum_salary",
        "maximum_salary"
    ]

    for column in numeric_columns:
        analysis_df[column] = pd.to_numeric(
            analysis_df[column],
            errors="coerce"
        )

    # Experience statistics
    experience_summary = {
        "experience_records": analysis_df[
            "minimum_experience"
        ].notna().sum(),

        "average_min_experience": analysis_df[
            "minimum_experience"
        ].mean(),

        "average_max_experience": analysis_df[
            "maximum_experience"
        ].mean()
    }

    # Salary statistics
    salary_summary = {
        "salary_records": analysis_df[
            "minimum_salary"
        ].notna().sum(),

        "average_min_salary": analysis_df[
            "minimum_salary"
        ].mean(),

        "average_max_salary": analysis_df[
            "maximum_salary"
        ].mean()
    }

    return experience_summary, salary_summary

def statistical_analysis(df):

    stats_df = df.copy()

    numeric_columns = [
        "minimum_experience",
        "maximum_experience",
        "minimum_salary",
        "maximum_salary",
        "aggregate_rating",
        "reviews_count"
    ]

    for column in numeric_columns:
        stats_df[column] = pd.to_numeric(
            stats_df[column],
            errors="coerce"
        )

    correlation_columns = [
        "minimum_experience",
        "maximum_experience",
        "minimum_salary",
        "maximum_salary",
        "aggregate_rating",
        "reviews_count"
    ]

    correlation_matrix = (
        stats_df[correlation_columns]
        .corr()
    )

    return correlation_matrix

def experience_salary_test(df):

    test_df = df[
        [
            "minimum_experience",
            "minimum_salary"
        ]
    ].copy()

    test_df["minimum_experience"] = pd.to_numeric(
        test_df["minimum_experience"],
        errors="coerce"
    )

    test_df["minimum_salary"] = pd.to_numeric(
        test_df["minimum_salary"],
        errors="coerce"
    )

    test_df = test_df.dropna()

    correlation, p_value = pearsonr(
        test_df["minimum_experience"],
        test_df["minimum_salary"]
    )

    return {
        "sample_size": len(test_df),
        "correlation": correlation,
        "p_value": p_value
    }

def experience_segmentation(df):

    segment_df = df.copy()

    segment_df["minimum_experience"] = pd.to_numeric(
        segment_df["minimum_experience"],
        errors="coerce"
    )

    segment_df = segment_df.dropna(
        subset=["minimum_experience"]
    )

    def classify_experience(years):

        if years <= 1:
            return "Entry Level"

        elif years <= 3:
            return "Junior"

        elif years <= 6:
            return "Mid Level"

        elif years <= 10:
            return "Senior"

        else:
            return "Lead / Expert"

    segment_df["experience_level"] = (
        segment_df["minimum_experience"]
        .apply(classify_experience)
    )

    result = (
        segment_df["experience_level"]
        .value_counts()
        .rename_axis("experience_level")
        .reset_index(name="job_postings")
    )

    return result

def market_demand_score(df):

    analysis_df = df.dropna(
        subset=["title", "company_name", "location"]
    ).copy()

    role_stats = (
        analysis_df
        .groupby("title")
        .agg(
            job_postings=("title", "count"),
            companies=("company_name", "nunique"),
            locations=("location", "nunique")
        )
        .reset_index()
    )

    # Normalize each demand component to 0–100
    for column in [
        "job_postings",
        "companies",
        "locations"
    ]:

        min_value = role_stats[column].min()
        max_value = role_stats[column].max()

        if max_value == min_value:
            role_stats[f"{column}_score"] = 100
        else:
            role_stats[f"{column}_score"] = (
                (role_stats[column] - min_value)
                / (max_value - min_value)
            ) * 100

    # Weighted market demand score
    role_stats["market_demand_score"] = (
        role_stats["job_postings_score"] * 0.50
        + role_stats["companies_score"] * 0.30
        + role_stats["locations_score"] * 0.20
    )

    role_stats = role_stats.sort_values(
        "market_demand_score",
        ascending=False
    )

    return role_stats

def recruitment_dashboard_metrics(df):

    metrics = {}

    metrics["total_job_postings"] = len(df)

    metrics["unique_companies"] = (
        df["company_name"]
        .dropna()
        .nunique()
    )

    metrics["unique_roles"] = (
        df["title"]
        .dropna()
        .nunique()
    )

    metrics["unique_locations"] = (
        df["location"]
        .dropna()
        .nunique()
    )

    metrics["skill_records"] = (
        df["tags_and_skills"]
        .notna()
        .sum()
    )

    metrics["salary_records"] = (
        df["minimum_salary"]
        .notna()
        .sum()
    )

    metrics["experience_records"] = (
        df["minimum_experience"]
        .notna()
        .sum()
    )

    metrics["remote_jobs"] = (
        df["location"]
        .astype(str)
        .str.contains(
            "remote",
            case=False,
            na=False
        )
        .sum()
    )

    return metrics

if __name__ == "__main__":

    df = load_job_market_data()

    print("\n===== ROLE INTELLIGENCE =====")

    result = role_analysis(df)

    print("\nTop 20 roles by job postings:\n")

    print(
        result.head(20).to_string()
    )

    print("\nTotal roles analyzed:")
    
    print("\n===== SKILL DEMAND =====")

    skills = skill_analysis(df)

    print(
        skills.to_string(index=False)
    )

    print(len(result))
    
    print("\n===== LOCATION INTELLIGENCE =====")

    locations = location_analysis(df)

    print(
        "\nTop 20 locations by job postings:\n"
    )

    print(
        locations.head(20).to_string()
    )

    print("\nTotal locations analyzed:")
    print(len(locations))
    
    print("\n===== EXPERIENCE & SALARY INTELLIGENCE =====")

    experience_summary, salary_summary = (
        experience_salary_analysis(df)
    )

    print("\nExperience Summary:")

    for key, value in experience_summary.items():
        print(f"{key}: {value}")

    print("\nSalary Summary:")

    for key, value in salary_summary.items():
        print(f"{key}: {value}")
        
    print("\n===== STATISTICAL ANALYSIS =====")

    correlation_matrix = statistical_analysis(df)

    print("\nCorrelation Matrix:\n")

    print(
        correlation_matrix.to_string()
)
    
    
    print("\n===== EXPERIENCE-SALARY HYPOTHESIS TEST =====")

    test_result = experience_salary_test(df)

    print(
        f"Sample size: {test_result['sample_size']:,}"
    )

    print(
        f"Pearson correlation: "
        f"{test_result['correlation']:.4f}"
    )

    print(
        f"P-value: "
        f"{test_result['p_value']:.10f}"
    )

    if test_result["p_value"] < 0.05:
        print(
            "Result: Statistically significant relationship"
        )
    else:
        print(
            "Result: Not statistically significant"
        )
        
    print("\n===== EXPERIENCE SEGMENTATION =====")

    experience_segments = experience_segmentation(df)

    print(
        experience_segments.to_string(index=False)
    )
    
    print("\n===== MARKET DEMAND SCORE =====")

    demand = market_demand_score(df)

    print(
        demand.head(20).to_string(index=False)
    )
    
    
    
    print("\n===== RECRUITMENT DASHBOARD METRICS =====")

    metrics = recruitment_dashboard_metrics(df)

    for key, value in metrics.items():

        print(
            f"{key}: {value:,}"
        )