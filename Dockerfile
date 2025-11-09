FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости (для catboost нужен libgomp1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# Питон-зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Код и артефакты модели
COPY preprocess.py predict.py kafka_worker.py db_writer.py app.py ./
COPY model.pkl features.json threshold.txt ./

# Опционально: порт UI (Streamlit)
EXPOSE 8501

# Никаких жёстких entrypoint'ов: команды задаются в docker-compose
# Для "пустого" контейнера оставим бездействующий CMD
CMD ["python", "-c", "import time; time.sleep(3600)"]
