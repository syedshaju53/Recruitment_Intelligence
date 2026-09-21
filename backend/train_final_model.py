import os
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBClassifier

from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)
from sklearn.model_selection import train_test_split

from backend.prepare_ml_dataset import prepare_ml_dataset


print("\n========================================")
print("     FINAL XGBOOST MODEL TRAINING")
print("========================================")


# ============================================================
# 1. PREPARE ML DATASET
# ============================================================

print("\n===== STEP 1: PREPARING ML DATASET =====")

ml_data = prepare_ml_dataset()

print("ML dataset shape:", ml_data.shape)


# ============================================================
# 2. DEFINE FINAL 10 FEATURES
# ============================================================

print("\n===== STEP 2: SELECTING FINAL FEATURES =====")

final_features = [
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

target = "demand_class"

print("\nFinal features:")

for feature in final_features:
    print("✓", feature)

print("\nTotal final features:", len(final_features))


# ============================================================
# 3. CREATE X AND y
# ============================================================

print("\n===== STEP 3: CREATING TRAINING DATA =====")

X = ml_data[final_features].copy()
y = ml_data[target].copy()

# Convert all final features to numeric values
# and convert Pandas <NA> values into NumPy NaN
for feature in final_features:
    X[feature] = pd.to_numeric(
        X[feature],
        errors="coerce"
    )

X = X.replace({pd.NA: np.nan})

print("\n===== FINAL FEATURE DATA TYPES =====")
print(X.dtypes)

print("\n===== FINAL MISSING VALUES =====")
print(X.isna().sum())

print("X shape:", X.shape)
print("y shape:", y.shape)


# ============================================================
# 4. TRAIN / TEST SPLIT
# ============================================================

print("\n===== STEP 4: TRAIN / TEST SPLIT =====")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training shape:", X_train.shape)
print("Testing shape :", X_test.shape)


# ============================================================
# 5. FINAL PREPROCESSING
# ============================================================

print("\n===== STEP 5: FINAL PREPROCESSING =====")

# Only the 10 final features are passed to the imputer.
# No salary_missing or experience_missing features are created.

imputer = SimpleImputer(
    strategy="median"
)

X_train_imputed = imputer.fit_transform(X_train)
X_test_imputed = imputer.transform(X_test)

X_train = pd.DataFrame(
    X_train_imputed,
    columns=final_features,
    index=X_train.index
)

X_test = pd.DataFrame(
    X_test_imputed,
    columns=final_features,
    index=X_test.index
)

print("✓ Missing values handled")

print(
    "\nRemaining missing values:",
    X_train.isnull().sum().sum()
)


# ============================================================
# 6. TRAIN FINAL XGBOOST
# ============================================================

print("\n===== STEP 6: TRAINING FINAL XGBOOST =====")

model = XGBClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=6,
    random_state=42,
    eval_metric="logloss",
    n_jobs=-1
)

model.fit(
    X_train,
    y_train
)

print("✓ XGBoost training completed")


# ============================================================
# 7. PREDICTIONS
# ============================================================

print("\n===== STEP 7: MODEL EVALUATION =====")

y_pred = model.predict(X_test)

y_probability = model.predict_proba(X_test)[:, 1]


# ============================================================
# 8. METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred
)

recall = recall_score(
    y_test,
    y_pred
)

f1 = f1_score(
    y_test,
    y_pred
)

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

cm = confusion_matrix(
    y_test,
    y_pred
)


print("\n===== FINAL MODEL PERFORMANCE =====")

print(f"Accuracy  : {accuracy:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")
print(f"ROC-AUC   : {roc_auc:.4f}")


# ============================================================
# 9. CONFUSION MATRIX
# ============================================================

print("\n===== CONFUSION MATRIX =====")

print(cm)


# ============================================================
# 10. FEATURE IMPORTANCE
# ============================================================

print("\n===== FINAL FEATURE IMPORTANCE =====")

feature_importance = pd.DataFrame({
    "feature": final_features,
    "importance": model.feature_importances_
})

feature_importance = feature_importance.sort_values(
    "importance",
    ascending=False
)

print(
    feature_importance.to_string(
        index=False
    )
)


# ============================================================
# 11. CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    "outputs",
    exist_ok=True
)


# ============================================================
# 12. SAVE FEATURE IMPORTANCE
# ============================================================

feature_importance.to_csv(
    "outputs/final_model_feature_importance.csv",
    index=False
)


# ============================================================
# 13. SAVE FINAL MODEL
# ============================================================

model_path = (
    "outputs/final_xgboost_model.pkl"
)

joblib.dump(
    model,
    model_path
)


# ============================================================
# 14. SAVE FINAL PREPROCESSING
# ============================================================

preprocessing = {
    "imputer": imputer,
    "features": final_features
}

preprocessing_path = (
    "outputs/final_preprocessing.pkl"
)

joblib.dump(
    preprocessing,
    preprocessing_path
)


# ============================================================
# 15. SAVE MODEL METRICS
# ============================================================

metrics = pd.DataFrame([
    {
        "model": "Final XGBoost",
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc
    }
])

metrics.to_csv(
    "outputs/final_model_metrics.csv",
    index=False
)


# ============================================================
# 16. FINAL SUMMARY
# ============================================================

print("\n========================================")
print("       FINAL MODEL COMPLETED")
print("========================================")

print("\nModel:")
print("XGBoost")

print("\nNumber of features:")
print(len(final_features))

print("\nROC-AUC:")
print(f"{roc_auc:.4f}")

print("\nF1 Score:")
print(f"{f1:.4f}")

print("\nSaved files:")

print("✓ outputs/final_xgboost_model.pkl")
print("✓ outputs/final_preprocessing.pkl")
print("✓ outputs/final_model_metrics.csv")
print("✓ outputs/final_model_feature_importance.csv")

print("\n========================================")