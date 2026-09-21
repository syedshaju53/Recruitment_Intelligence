import os
import joblib
import pandas as pd

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"]
)


# ============================================================
# LOAD FINAL MODEL
# ============================================================

MODEL_PATH = "outputs/final_xgboost_model.pkl"
PREPROCESSING_PATH = "outputs/final_preprocessing.pkl"


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

if not os.path.exists(PREPROCESSING_PATH):
    raise FileNotFoundError(
        f"Preprocessing not found: {PREPROCESSING_PATH}"
    )


model = joblib.load(
    MODEL_PATH
)

preprocessing = joblib.load(
    PREPROCESSING_PATH
)


imputer = preprocessing["imputer"]
features = preprocessing["features"]


print("✓ Final XGBoost model loaded")
print("✓ Final preprocessing loaded")
print("✓ Features:", features)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class MLPredictionRequest(BaseModel):

    minimum_experience: float
    maximum_experience: float

    salary_midpoint: float | None = None
    experience_midpoint: float

    salary_range: float | None = None
    experience_range: float

    skill_count: int
    is_remote: int

    title_length: int
    company_name_length: int


# ============================================================
# PREDICTION ENDPOINT
# ============================================================

@router.post("/predict")
def predict_demand(
    request: MLPredictionRequest
):

    # --------------------------------------------------------
    # Create input dataframe
    # --------------------------------------------------------

    input_data = {
        "minimum_experience": request.minimum_experience,
        "maximum_experience": request.maximum_experience,
        "salary_midpoint": request.salary_midpoint,
        "experience_midpoint": request.experience_midpoint,
        "salary_range": request.salary_range,
        "experience_range": request.experience_range,
        "skill_count": request.skill_count,
        "is_remote": request.is_remote,
        "title_length": request.title_length,
        "company_name_length": request.company_name_length
    }

    df = pd.DataFrame(
        [input_data]
    )

    # --------------------------------------------------------
    # Ensure exact feature order
    # --------------------------------------------------------

    df = df[features]

    # --------------------------------------------------------
    # Convert values to numeric
    # --------------------------------------------------------

    for feature in features:

        df[feature] = pd.to_numeric(
            df[feature],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Apply final preprocessing
    # --------------------------------------------------------

    df_imputed = imputer.transform(
        df
    )

    X = pd.DataFrame(
        df_imputed,
        columns=features
    )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    prediction = int(
        model.predict(X)[0]
    )

    probabilities = model.predict_proba(X)[0]

    probability = float(
        probabilities[1]
    )

    # --------------------------------------------------------
    # Demand class
    # --------------------------------------------------------

    if prediction == 1:

        demand_class = "High Demand"

    else:

        demand_class = "Low Demand"

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "prediction": prediction,
        "demand_class": demand_class,
        "probability": round(
            probability,
            4
        ),
        "class_0_probability": round(
            float(probabilities[0]),
            4
        ),
        "class_1_probability": round(
            float(probabilities[1]),
            4
        )
    }