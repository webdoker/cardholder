FROM python:3.11-slim

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY app/ .

# Запускаем приложение
CMD ["python", "main.py"]