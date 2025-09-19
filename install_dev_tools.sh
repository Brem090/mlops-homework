#!/bin/bash

# --- Змінні ---
LOG_FILE="install.log"
PYTHON_VERSION_REQUIRED_MAJOR=3
PYTHON_VERSION_REQUIRED_MINOR=9

# --- Логування в файл та консоль ---
> "$LOG_FILE"
exec &> >(tee -a "$LOG_FILE")

echo "Початок налаштування середовища | $(date)"
echo "================================================="

# --- Функція для перевірки версії Python ---
check_python_version() {
    PYTHON_VERSION_INSTALLED=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_VERSION_MAJOR=$(echo "$PYTHON_VERSION_INSTALLED" | cut -d. -f1)
    PYTHON_VERSION_MINOR=$(echo "$PYTHON_VERSION_INSTALLED" | cut -d. -f2)

    if [ "$PYTHON_VERSION_MAJOR" -lt "$PYTHON_VERSION_REQUIRED_MAJOR" ] || \
       { [ "$PYTHON_VERSION_MAJOR" -eq "$PYTHON_VERSION_REQUIRED_MAJOR" ] && [ "$PYTHON_VERSION_MINOR" -lt "$PYTHON_VERSION_REQUIRED_MINOR" ]; }; then
        echo "Помилка: Встановлена версія Python ($PYTHON_VERSION_INSTALLED) старіша за необхідну ($PYTHON_VERSION_REQUIRED_MAJOR.$PYTHON_VERSION_REQUIRED_MINOR)."
        return 1
    fi

    echo "Версія Python ($PYTHON_VERSION_INSTALLED) відповідає вимогам (>= $PYTHON_VERSION_REQUIRED_MAJOR.$PYTHON_VERSION_REQUIRED_MINOR)."
    return 0
}

# --- Перевірка та встановлення інструментів ---

# 1. Docker
if command -v docker &> /dev/null; then
    echo "Docker вже встановлено."
else
    echo "Встановлення Docker..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
    sudo usermod -aG docker $USER
    echo "Docker встановлено. Перелогіньтесь, щоб зміни групи вступили в силу."
fi

# 2. Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose вже встановлено."
else
    echo "Встановлення Docker Compose..."
    sudo apt-get install -y docker-compose-plugin
fi

# 3. Python 3 та pip
if command -v python3 &> /dev/null && command -v pip3 &> /dev/null; then
    echo "Python 3 та pip вже встановлено."
    check_python_version || exit 1
else
    echo "Встановлення Python 3 та pip..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# 4. Встановлення Python бібліотек у ізольоване venv
echo "Готуємо віртуальне середовище..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -U pip setuptools wheel

echo "Перевірка та встановлення Python бібліотек..."
pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.2,<3.0" "torchvision>=0.17,<1.0"
pip install pillow django

# --- Перевірка версій ---
echo "================================================="
echo "Перевірка версій встановлених інструментів:"
echo "-------------------------------------------------"
echo "Docker version:"; docker --version
echo "Docker Compose version:"; docker compose version
echo "Python version:"; python --version
echo "pip version:"; pip --version
echo "-------------------------------------------------"
echo "Версії Python бібліотек:"
python - <<'PY'
import torch, PIL, django, torchvision
print("torch:", torch.__version__, "| CUDA:", torch.cuda.is_available())
print("torchvision:", torchvision.__version__)
print("Pillow:", PIL.__version__)
print("Django:", django.get_version())
PY
echo "================================================="
echo "Налаштування середовища завершено. Лог збережено у файлі $LOG_FILE"
