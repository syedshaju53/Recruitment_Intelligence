import pandas as pd

from sklearn.model_selection import cross_val_score
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from backend.prepare_ml_dataset import prepare_ml_dataset
from backend.ml_preprocessing import prepare_training_data


print("\n===== LOADING AND PREPROCESSING DATA =====")

ml_data = prepare_ml_dataset()

X_train, X_test, y_train, y_test, imputer, scaler = prepare_training_data(
    ml_data
)


models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    ),

    "XGBoost": XGBClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1
    )
}


results = []


print("\n===== MODEL VALIDATION =====")


for model_name, model in models.items():

    print(f"\nTraining: {model_name}")

    # Train
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)

    # Probabilities
    y_prob = model.predict_proba(X_test)[:, 1]

    # Metrics
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
        y_prob
    )

    # 5-fold cross validation
    cv_scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=5,
        scoring="accuracy",
        n_jobs=-1
    )

    results.append({
        "Model": model_name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1,
        "ROC-AUC": roc_auc,
        "CV Mean Accuracy": cv_scores.mean(),
        "CV Std": cv_scores.std()
    })


# Convert results to DataFrame
results_df = pd.DataFrame(results)


# Sort by ROC-AUC
results_df = results_df.sort_values(
    by="ROC-AUC",
    ascending=False
)


print("\n===== FINAL MODEL COMPARISON =====")

print(
    results_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# Best model
best_model = results_df.iloc[0]


print("\n===== BEST MODEL =====")

print(
    f"Model: {best_model['Model']}"
)

print(
    f"ROC-AUC: {best_model['ROC-AUC']:.4f}"
)

print(
    f"Accuracy: {best_model['Accuracy']:.4f}"
)

print(
    f"Precision: {best_model['Precision']:.4f}"
)

print(
    f"Recall: {best_model['Recall']:.4f}"
)

print(
    f"F1 Score: {best_model['F1 Score']:.4f}"
)

print(
    f"CV Mean Accuracy: {best_model['CV Mean Accuracy']:.4f}"
)

print(
    f"CV Std: {best_model['CV Std']:.4f}"
)


# Save results
results_df.to_csv(
    "outputs/model_comparison.csv",
    index=False
)


print("\nModel comparison saved:")
print("outputs/model_comparison.csv")