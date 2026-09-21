from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

from backend.prepare_ml_dataset import prepare_ml_dataset
from backend.ml_preprocessing import prepare_training_data


print("\n===== FEATURE ABLATION TEST =====")


# ============================================================
# STEP 1 — PREPARE ML DATASET
# ============================================================

ml_data = prepare_ml_dataset()

print("\n===== ORIGINAL ML DATASET SHAPE =====")
print(ml_data.shape)


# ============================================================
# STEP 2 — PREPROCESS DATA
# This is where salary_missing is created
# ============================================================

X_train, X_test, y_train, y_test, imputer, scaler = prepare_training_data(
    ml_data
)


print("\n===== DATA BEFORE ABLATION =====")
print("X_train columns:")
print(X_train.columns.tolist())

print("\nX_test columns:")
print(X_test.columns.tolist())


# ============================================================
# STEP 3 — CHECK SALARY MISSING FEATURE
# ============================================================

if "salary_missing" not in X_train.columns:

    print("\nERROR: salary_missing feature was not created.")

    print("\nAvailable features:")
    print(X_train.columns.tolist())

    raise SystemExit


print("\n===== REMOVING SALARY_MISSING =====")

X_train = X_train.drop(columns=["salary_missing"])
X_test = X_test.drop(columns=["salary_missing"])


print("\n===== DATA AFTER ABLATION =====")
print("X_train shape:", X_train.shape)
print("X_test shape:", X_test.shape)

print("\nRemaining features:")
print(X_train.columns.tolist())


# ============================================================
# STEP 4 — DEFINE MODELS
# ============================================================

models = {

    "Logistic Regression":
        LogisticRegression(
            max_iter=1000,
            random_state=42
        ),

    "Random Forest":
        RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            n_jobs=-1
        ),

    "XGBoost":
        XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            random_state=42,
            eval_metric="logloss",
            n_jobs=-1
        )
}


# ============================================================
# STEP 5 — TRAIN & EVALUATE
# ============================================================

results = []


for name, model in models.items():

    print(f"\n===== TRAINING {name} =====")

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions
    )

    recall = recall_score(
        y_test,
        predictions
    )

    f1 = f1_score(
        y_test,
        predictions
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities
    )

    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print(f"ROC-AUC   : {roc_auc:.4f}")

    results.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1,
        "ROC-AUC": roc_auc
    })


# ============================================================
# STEP 6 — SAVE RESULTS
# ============================================================

import pandas as pd
import os

results_df = pd.DataFrame(results)

print("\n===== FEATURE ABLATION RESULTS =====")
print(results_df.to_string(index=False))


os.makedirs("outputs", exist_ok=True)

results_df.to_csv(
    "outputs/feature_ablation_results.csv",
    index=False
)

print(
    "\nResults saved to:"
    " outputs/feature_ablation_results.csv"
)