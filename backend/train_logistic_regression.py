import joblib

from sklearn.linear_model import LogisticRegression
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


def train_logistic_regression():

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

    print("\n===== TRAINING LOGISTIC REGRESSION =====")

    model = LogisticRegression(
        max_iter=1000,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    print("Model training completed.")

    # Predictions
    y_pred = model.predict(X_test)

    # Probabilities
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

    print("\n===== LOGISTIC REGRESSION RESULTS =====")

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

    train_logistic_regression()