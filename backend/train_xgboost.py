import joblib

from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from backend.prepare_ml_dataset import prepare_ml_dataset
from backend.ml_preprocessing import prepare_training_data


def train_xgboost():

    print("\n===== LOADING ML DATASET =====")

    ml_data = prepare_ml_dataset()

    (
        X_train,
        X_test,
        y_train,
        y_test,
        imputer,
        scaler
    ) = prepare_training_data(ml_data)

    print("\n===== TRAINING XGBOOST =====")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )

    print("Model training completed.")

    # Predictions
    y_pred = model.predict(X_test)

    # Probability of class 1
    y_probability = model.predict_proba(X_test)[:, 1]

    # Evaluation
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

    print("\n===== XGBOOST RESULTS =====")

    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")

    print("\n===== CLASSIFICATION REPORT =====")

    print(
        classification_report(
            y_test,
            y_pred
        )
    )

    print("\n===== CONFUSION MATRIX =====")

    print(
        confusion_matrix(
            y_test,
            y_pred
        )
    )

    print("\n===== FEATURE IMPORTANCE =====")

    feature_importance = sorted(
        zip(
            X_train.columns,
            model.feature_importances_
        ),
        key=lambda x: x[1],
        reverse=True
    )

    for feature, importance in feature_importance:

        print(
            f"{feature:25s} : {importance:.4f}"
        )

    print("\n===== SAMPLE PREDICTIONS =====")

    for actual, predicted, probability in zip(
        y_test.head(10),
        y_pred[:10],
        y_probability[:10]
    ):

        print(
            f"Actual: {actual} | "
            f"Predicted: {predicted} | "
            f"Probability: {probability:.4f}"
        )

    return (
        model,
        imputer,
        scaler,
        accuracy,
        precision,
        recall,
        f1
    )


if __name__ == "__main__":

    train_xgboost()