# GitOps з ArgoCD та MLflow (локальний кластер Docker Desktop)

## Огляд проєкту

Цей проєкт демонструє практичну реалізацію **GitOps-підходу** для автоматизованого розгортання MLflow за допомогою ArgoCD. Інфраструктура розгорнута у **локальному Kubernetes-кластері Docker Desktop**, що дозволяє безпечно відпрацювати всі етапи без витрат на хмарні ресурси.
Архітектура проєкту відтворює логіку, призначену для AWS EKS, але адаптована під локальне середовище.

## Архітектура рішення

- **Docker Desktop Kubernetes** — локальний кластер для розгортання сервісів
- **ArgoCD** (namespace `infra-tools`) — інструмент GitOps, розгорнутий через Terraform
- **MLflow Application** — декларативний опис у Git-репозиторії, який синхронізує ArgoCD
- **MLflow Tracking Server** — сервіс у namespace `mlflow`, доступний через порт `5000`

## Структура репозиторію

```
mlflow-gitops/
├── terraform/
│   └── argocd/
│       ├── backend.tf
│       ├── main.tf
│       ├── terraform.tf
│       ├── variables.tf
│       └── values/
│           └── argocd-values.yaml
├── mlflow/
│   └── application.yaml
└── namespaces/
    └── mlflow-ns.yaml
```

### Опис директорій

- `terraform/argocd` — Terraform-модуль для розгортання ArgoCD
- `mlflow/application.yaml` — декларативний опис ArgoCD Application з вбудованою конфігурацією Helm (values)
- `namespaces/mlflow-ns.yaml` — визначення namespace

> **Важливо:** Всі налаштування MLflow (включно з backend store) вбудовані безпосередньо в `application.yaml`, окремий файл `values.yaml` не потрібен.

## Конфігурація ArgoCD Application

Файл `mlflow/application.yaml` описує ArgoCD Application з **вбудованою конфігурацією Helm**:

**Git-репозиторій з конфігурацією:** https://github.com/Brem090/my-mlops-apps.git

**Helm chart:** https://community-charts.github.io/helm-charts (chart `mlflow` версії 0.7.16)

Повна конфігурація в `application.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mlflow
  namespace: infra-tools
spec:
  project: default
  source:
    repoURL: 'https://community-charts.github.io/helm-charts'
    chart: mlflow
    targetRevision: 0.7.16
    helm:
      values: |
        backend_store:
          type: sqlite
  destination:
    server: https://kubernetes.default.svc
    namespace: mlflow
  syncPolicy:
    automated:
      prune: true      
      selfHeal: true    
    syncOptions:
      - CreateNamespace=true
```

### Як працює GitOps-підхід у цьому проєкті

1. Файл `application.yaml` зберігається у вашому Git-репозиторії з усіма налаштуваннями
2. ArgoCD підхоплює Helm chart з публічного репозиторію community-charts
3. ArgoCD застосовує вбудовані налаштування (`values`) до chart
4. При змінах `application.yaml` у Git ArgoCD автоматично синхронізує стан кластера
5. Всі зміни конфігурації відстежуються через Git-історію

> **Примітка:** У цій архітектурі всі налаштування (включно з `backend_store`) вбудовані безпосередньо в `application.yaml`, що робить конфігурацію більш компактною та самодостатньою.

Необхідно встановити:

- **Docker Desktop** з увімкненим Kubernetes
- **Terraform** (версія 1.5.0 або вище)
- **kubectl**

### Перевірка підключення

```bash
kubectl get nodes
```

Очікуваний результат: вузол `docker-desktop` у статусі `Ready`.


## Інструкція з розгортання

### Крок 1. Розгортання ArgoCD

```bash
cd terraform\argocd
terraform init
terraform apply -auto-approve
```

Перевірка успішності розгортання:

```bash
kubectl get pods -n infra-tools
```

Очікуваний результат: pod-и з префіксом `argocd-` у статусі `Running`.

### Крок 2. Доступ до ArgoCD UI

**Відкрийте новий термінал** та налаштуйте port-forward для доступу до інтерфейсу:

```bash
kubectl port-forward svc/argocd-server -n infra-tools 8080:443
```

> **Важливо:** Залишіть цей термінал відкритим — port-forward має працювати постійно для доступу до ArgoCD UI.

Відкрийте браузер за адресою: **http://localhost:8080**

**У третьому терміналі** отримайте пароль адміністратора:

**Для PowerShell:**
```powershell
[System.Text.Encoding]::UTF8.GetString(
  [System.Convert]::FromBase64String(
    (kubectl -n infra-tools get secret argocd-initial-admin-secret -o jsonpath='{.data.password}')
  )
)
```

**Для Linux/macOS:**
```bash
kubectl -n infra-tools get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode
```

- **Логін:** `admin`
- **Пароль:** результат виконання команди

### Крок 3. Розгортання MLflow

**Поверніться до першого терміналу** (або відкрийте четвертий) та застосуйте конфігурацію:

```bash
kubectl apply -f mlflow\application.yaml -n infra-tools
```

ArgoCD автоматично підхопить конфігурацію з Git-репозиторію, вказаного у `application.yaml`.

**Перевірка статусу деплою через CLI:**

```bash
# Перевірити статус Application
kubectl get application mlflow -n infra-tools

# Перевірити деталі синхронізації
kubectl describe application mlflow -n infra-tools
```

**Перевірка через UI:**

У веб-інтерфейсі ArgoCD (http://localhost:8080) ви побачите:
- Застосунок `mlflow` у списку Applications
- Статус має бути **Synced** (зелена галочка) — конфігурація синхронізована з Git
- Статус має бути **Healthy** (зелене серце) — всі ресурси працюють коректно

> **Підказка:** Клацніть на застосунок `mlflow` у UI ArgoCD, щоб побачити візуальну схему всіх розгорнутих ресурсів Kubernetes.

### Крок 4. Перевірка роботи MLflow

Переконайтеся, що всі ресурси створені:

```bash
kubectl get pods -n mlflow
kubectl get svc -n mlflow
```

**Відкрийте ще один новий термінал** та налаштуйте доступ до MLflow:

```bash
kubectl port-forward svc/mlflow -n mlflow 5000:5000
```

> **Важливо:** Залишіть цей термінал відкритим — port-forward має працювати для доступу до MLflow UI.

Відкрийте браузер за адресою: **http://localhost:5000**

### Підсумок активних терміналів

Після завершення всіх кроків у вас має бути:

- **Термінал 1:** Вільний для виконання команд
- **Термінал 2:** Port-forward для ArgoCD (порт 8080)
- **Термінал 3:** Port-forward для MLflow (порт 5000)

## Очищення ресурсів

Для видалення всіх створених ресурсів:

```bash
# Видалення MLflow Application
kubectl delete application mlflow -n infra-tools
kubectl delete ns mlflow

# Видалення ArgoCD через Terraform
cd terraform\argocd
terraform destroy -auto-approve
```

За потреби можна вимкнути Kubernetes у Docker Desktop: **Settings → Kubernetes → зняти прапорець "Enable Kubernetes"**

## Результати роботи

Після успішного розгортання ви отримаєте:

- **ArgoCD** у namespace `infra-tools` → http://localhost:8080
- **MLflow Tracking Server** у namespace `mlflow` → http://localhost:5000
- Повністю функціональну GitOps-інфраструктуру з автоматичною синхронізацією змін

## Висновок

Проєкт демонструє повноцінну реалізацію GitOps-підходу у **локальному середовищі Docker Desktop**. README повністю адаптовано під Windows PowerShell з альтернативними командами для Linux/macOS. Це дозволяє безпечно та без витрат відпрацювати інтеграцію ArgoCD та MLflow.