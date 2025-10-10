**Автоматизоване тренування моделей: MLOps-проєкт на базі AWS Lambda, Step Functions і GitHub Actions**

---

## Опис проєкту

Цей проєкт демонструє повну автоматизацію процесу тренування ML-моделей — від створення інфраструктури до налаштування CI/CD тригерів.

### Що робить проєкт?

За допомогою Terraform створюється автоматизований пайплайн у AWS, який виконує послідовність кроків:

1. **ValidateData** — перевірка даних перед тренуванням (Lambda #1)
2. **LogMetrics** — логування результатів та метрик (Lambda #2)
3. **Step Function** — координує виконання всіх етапів
4. **GitHub Actions** — автоматично запускає пайплайн при push у гілку `lesson-10`

---

## Архітектура рішення

```text
┌─────────────────┐
│ GitHub Actions  │
└────────┬────────┘
         │ trigger
         ▼
┌─────────────────────────────┐
│ AWS Step Function           │
│ (TrainModelPipeline)        │
└─────────────┬───────────────┘
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
┌──────────┐      ┌──────────┐
│ Lambda 1 │      │ Lambda 2 │
│ Validate │      │   Log    │
│   Data   │      │ Metrics  │
└──────────┘      └──────────┘
```

### Ключові компоненти:

- **Terraform** — описує всю інфраструктуру (IAM-ролі, Lambda-функції, Step Functions)
- **AWS Lambda** — виконує бізнес-логіку (валідація даних, логування)
- **AWS Step Functions** — керує послідовністю виконання завдань
- **GitHub Actions** — забезпечує автоматичний запуск пайплайна
- **CloudWatch** — зберігає логи та забезпечує моніторинг

---

## Технологічний стек

| Компонент | Призначення |
|-----------|-------------|
| **Terraform** | Infrastructure as Code — керування інфраструктурою |
| **AWS Lambda** | Виконання Python-функцій |
| **AWS Step Functions** | Оркестрація кроків пайплайна |
| **GitHub Actions** | CI/CD тригер для автоматизації |
| **CloudWatch** | Логування подій та моніторинг |

---

## Запуск проєкту

### 1. Підготовка Lambda-функцій

Перед деплоєм потрібно створити `.zip`-архіви для AWS Lambda:

```bash
cd terraform/lambda
```

**Windows (PowerShell):**
```powershell
Compress-Archive -Path validate.py -DestinationPath validate.zip -Force
Compress-Archive -Path log_metrics.py -DestinationPath log_metrics.zip -Force
```

**Linux/macOS:**
```bash
zip validate.zip validate.py
zip log_metrics.zip log_metrics.py
```

### 2. Розгортання інфраструктури через Terraform

```bash
cd terraform
terraform init
terraform apply
```

Terraform створить наступні ресурси:

- 2 Lambda-функції: `validate-fn`, `log-metrics-fn`
- IAM-ролі з необхідними політиками доступу
- Step Function з назвою `TrainModelPipeline`

### 3. Перевірка роботи в AWS Console

1. Перейдіть до **AWS Step Functions** → оберіть `TrainModelPipeline`
2. Натисніть **Start Execution**
3. Введіть тестовий JSON:

```json
{
  "source": "manual",
  "commit": "test"
}
```

4. Переконайтеся, що обидва кроки (`ValidateData`, `LogMetrics`) виконались успішно

**Перегляд логів:** AWS CloudWatch → Log groups → `/aws/lambda/validate-fn` та `/aws/lambda/log-metrics-fn`

---

## Інтеграція з GitHub Actions

Workflow-файл `train.yml` знаходиться в `.github/workflows/`.

```yaml
on:
  push:
    branches: 
      - main
      - lesson-10
```

### Як працює автоматизація?

При кожному `git push` у гілку `lesson-10`, GitHub Actions:

1. Підключається до AWS через credentials
2. Запускає Step Function `TrainModelPipeline`
3. Передає метадані про коміт у пайплайн

Результати виконання можна переглянути в розділі **Actions** репозиторію на GitHub.

---

## Структура проєкту

```
mlops-train-automation/
├── .github/
│   └── workflows/
│       └── train.yml          # GitHub Actions workflow
├── terraform/
│   ├── main.tf                # Основний конфігураційний файл
│   ├── variables.tf           # Змінні Terraform
│   └── lambda/
│       ├── validate.py        # Lambda-функція валідації
│       ├── validate.zip       # Архів для деплою
│       ├── log_metrics.py     # Lambda-функція логування
│       └── log_metrics.zip    # Архів для деплою
├── .gitignore
└── README.md
```

---

## Результати виконання

Всі етапи проєкту успішно виконано та протестовано:

- **Розгортання Terraform** — інфраструктура створена успішно
- **Lambda-функції** — обидві функції (`validate-fn`, `log-metrics-fn`) працюють коректно
- **Step Function (ручний запуск)** — виконання завершилось зі статусом `SUCCEEDED`
- **GitHub Actions (автоматичний запуск)** — workflow спрацьовує автоматично при push, статус `SUCCEEDED`
- **CloudWatch логи** — містять очікувані повідомлення: `Validating data...` та `Logging metrics...`

---

## Підсумок

Проєкт реалізує повний цикл автоматизованого тренування ML-моделей, включаючи створення інфраструктури через Terraform, виконання етапів через AWS Step Functions, інтеграцію CI/CD з GitHub Actions та логування з моніторингом через CloudWatch.

Усі ресурси створені в межах AWS Free Tier. 

---