import os
import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss, confusion_matrix
import numpy as np
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import shutil
import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt
import seaborn as sns

# Конфігурація MLflow
MLFLOW_TRACKING_URI = "http://localhost:5000"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9001"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin123"

# Конфігурація PushGateway
PUSHGATEWAY_URL = "localhost:9092"

# Налаштування MLflow
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("iris-classification")


def load_data():
    """Завантаження та підготовка датасету Iris (з ускладненням)"""
    iris = load_iris()
    X = iris.data
    y = iris.target

    # Додаємо шум у фічі (імітація реальніших вимірювань)
    rng = np.random.default_rng()
    noise = rng.normal(0, 0.3, X.shape)
    X_noisy = X + noise

    # Випадковий random_state для кожного виклику
    random_state = np.random.randint(0, 10000)
    X_train, X_test, y_train, y_test = train_test_split(
        X_noisy, y, test_size=0.4, random_state=random_state, stratify=y
    )

    print(f"✓ Використано random_state={random_state}")
    return X_train, X_test, y_train, y_test


def push_metrics_to_prometheus(run_id, accuracy, loss):
    """Відправка метрик у Prometheus PushGateway"""
    registry = CollectorRegistry()

    # Створення метрик
    accuracy_gauge = Gauge('mlflow_accuracy', 'Model accuracy', ['run_id'], registry=registry)
    loss_gauge = Gauge('mlflow_loss', 'Model loss', ['run_id'], registry=registry)

    # Встановлення значень
    accuracy_gauge.labels(run_id=run_id).set(accuracy)
    loss_gauge.labels(run_id=run_id).set(loss)

    # Відправка в PushGateway
    try:
        push_to_gateway(PUSHGATEWAY_URL, job='mlflow_experiments', registry=registry)
        print(f"✓ Метрики відправлені в PushGateway для run_id: {run_id}")
    except Exception as e:
        print(f"✗ Помилка відправки метрик: {e}")


def save_confusion_matrix(y_true, y_pred, run_id):
    """Побудова та збереження матриці плутанини"""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    img_path = f"confusion_matrix_{run_id}.png"
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    mlflow.log_artifact(img_path)
    os.remove(img_path)


def train_model(n_estimators, max_depth, learning_rate, X_train, X_test, y_train, y_test):
    """Тренування моделі з заданими параметрами"""
    with mlflow.start_run() as run:
        params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
        }
        mlflow.log_params(params)

        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=np.random.randint(0, 10000)
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        loss = log_loss(y_test, y_pred_proba)

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("loss", loss)

        # Збереження моделі
        mlflow.sklearn.log_model(model, artifact_path="model")

        # Логування матриці плутанини
        save_confusion_matrix(y_test, y_pred, run.info.run_id)

        print(f"Run ID: {run.info.run_id}")
        print(f"  Parameters: n_estimators={n_estimators}, max_depth={max_depth}, lr={learning_rate}")
        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Loss: {loss:.4f}")

        push_metrics_to_prometheus(run.info.run_id, accuracy, loss)

        return run.info.run_id, accuracy, loss


def find_best_model(experiment_name):
    """Знаходження найкращої моделі за accuracy"""
    experiment = mlflow.get_experiment_by_name(experiment_name)
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.accuracy DESC"],
        max_results=1
    )

    if len(runs) == 0:
        print("Не знайдено жодного запуску!")
        return None

    best_run = runs.iloc[0]
    return best_run


def copy_best_model(run_id):
    """Копіювання найкращої моделі"""
    model_uri = f"runs:/{run_id}/model"
    best_model_dir = "../best_model"

    if os.path.exists(best_model_dir):
        for item in os.listdir(best_model_dir):
            if item != ".gitkeep":
                item_path = os.path.join(best_model_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

    model = mlflow.sklearn.load_model(model_uri)
    mlflow.sklearn.save_model(model, best_model_dir)
    print(f"✓ Найкраща модель збережена в {best_model_dir}")


def main():
    print("=" * 80)
    print("Початок експериментів з MLflow + Prometheus")
    print("=" * 80)

    print("\n[1/4] Завантаження датасету Iris...")

    # Параметри для експериментів
    experiments_params = [
        {"n_estimators": 50, "max_depth": 3, "learning_rate": 0.01},
        {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.05},
        {"n_estimators": 150, "max_depth": 7, "learning_rate": 0.1},
        {"n_estimators": 200, "max_depth": 10, "learning_rate": 0.15},
        {"n_estimators": 100, "max_depth": None, "learning_rate": 0.1},
    ]

    print(f"\n[2/4] Тренування {len(experiments_params)} моделей...")
    print("-" * 80)

    results = []
    for i, params in enumerate(experiments_params, 1):
        print(f"\nЕксперимент {i}/{len(experiments_params)}:")
        np.random.seed(i * 1234)
        X_train, X_test, y_train, y_test = load_data()
        run_id, accuracy, loss = train_model(
            params["n_estimators"],
            params["max_depth"],
            params["learning_rate"],
            X_train, X_test, y_train, y_test
        )
        results.append({
            "run_id": run_id,
            "accuracy": accuracy,
            "loss": loss,
            **params
        })

    print("\n" + "-" * 80)
    print("✓ Всі моделі натреновані!")

    print("\n[3/4] Пошук найкращої моделі...")
    best_run = find_best_model("iris-classification")

    if best_run is not None:
        print(f"\n{'=' * 80}")
        print("НАЙКРАЩА МОДЕЛЬ:")
        print(f"{'=' * 80}")
        print(f"Run ID: {best_run['run_id']}")
        print(f"Accuracy: {best_run['metrics.accuracy']:.4f}")
        print(f"Loss: {best_run['metrics.loss']:.4f}")
        print(f"Parameters:")
        print(f"  - n_estimators: {best_run['params.n_estimators']}")
        print(f"  - max_depth: {best_run['params.max_depth']}")
        print(f"  - learning_rate: {best_run['params.learning_rate']}")
        print(f"{'=' * 80}")

        print("\n[4/4] Копіювання найкращої моделі...")
        copy_best_model(best_run['run_id'])

        print("\n" + "=" * 80)
        print("ЕКСПЕРИМЕНТИ ЗАВЕРШЕНО УСПІШНО!")
        print("=" * 80)
        print("\nНаступні кроки:")
        print("1. Перегляньте експерименти в MLflow UI: http://localhost:5000")
        print("2. Перегляньте метрики в Grafana: http://localhost:30300")
        print("3. Найкраща модель збережена в директорії: ../best_model/")
    else:
        print("✗ Не вдалося знайти найкращу модель")


if __name__ == "__main__":
    main()
