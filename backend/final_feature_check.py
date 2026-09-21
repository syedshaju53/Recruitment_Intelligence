import pandas as pd

from backend.prepare_ml_dataset import prepare_ml_dataset
from backend.ml_preprocessing import prepare_training_data

from xgboost import XGBClassifier
from sklearn.inspection import permutation_importance


print("\n===== FINAL FEATURE CHECK =====")


# ============================================================
# 1. PREPARE DATA
# ============================================================

ml_data = prepare_ml_dataset()

X_train, X_test, y_train, y_test, imputer, scaler = prepare_training_data(
    ml_data
)

print("\n===== ORIGINAL FEATURES =====")
print(X_train.columns.tolist())


# ============================================================
# 2. REMOVE SALARY_MISSING
# ============================================================

if "salary_missing" in X_train.columns:
    X_train = X_train.drop(columns=["salary_missing"])
    X_test = X_test.drop(columns=["salary_missing"])

print("\n===== FINAL FEATURES =====")
print(X_train.columns.tolist())


# ============================================================
# 3. TRAIN XGBOOST
# ============================================================

model = XGBClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=6,
    random_state=42,
    eval_metric="logloss",
    n_jobs=-1
)

print("\n===== TRAINING FINAL XGBOOST =====")

model.fit(X_train, y_train)


# ============================================================
# 4. BUILT-IN FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({
    "feature": X_train.columns,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n===== XGBOOST FEATURE IMPORTANCE =====")
print(importance.to_string(index=False))


# ============================================================
# 5. PERMUTATION IMPORTANCE
# ============================================================

print("\n===== CALCULATING PERMUTATION IMPORTANCE =====")

perm = permutation_importance(
    model,
    X_test,
    y_test,
    n_repeats=5,
    random_state=42,
    scoring="roc_auc",
    n_jobs=-1
)

permutation_df = pd.DataFrame({
    "feature": X_test.columns,
    "importance_mean": perm.importances_mean,
    "importance_std": perm.importances_std
})

permutation_df = permutation_df.sort_values(
    "importance_mean",
    ascending=False
)

print("\n===== PERMUTATION IMPORTANCE =====")
print(permutation_df.to_string(index=False))


# ============================================================
# 6. SAVE RESULTS
# ============================================================

import os

os.makedirs("outputs", exist_ok=True)

importance.to_csv(
    "outputs/final_xgboost_feature_importance.csv",
    index=False
)

permutation_df.to_csv(
    "outputs/permutation_importance.csv",
    index=False
)


print("\n===== RESULTS SAVED =====")

print(
    "outputs/final_xgboost_feature_importance.csv"
)

print(
    "outputs/permutation_importance.csv"
)
