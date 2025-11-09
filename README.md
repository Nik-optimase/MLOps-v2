

# Fraud Scoring Service

## Описание

Проект реализует потоковый сервис скоринга транзакций с использованием Kafka, PostgreSQL и Streamlit.
Сервис читает входящие транзакции из Kafka, выполняет препроцессинг и скоринг с помощью модели машинного обучения,
записывает результаты в Kafka и PostgreSQL, а также предоставляет интерфейс для визуализации результатов.

---

## Архитектура

```
Kafka topic "transactions"  →  kafka_worker.py  →  Kafka topic "scores"
                                              ↓
                                           db_writer.py  →  PostgreSQL (таблица scores)
                                              ↓
                                             app.py  →  Streamlit-интерфейс
```

---

## Компоненты

| Файл                 | Назначение                                                                |
| -------------------- | ------------------------------------------------------------------------- |
| `Dockerfile`         | Сборка контейнера со всеми зависимостями                                  |
| `docker-compose.yml` | Поднимает все сервисы (Kafka, Zookeeper, PostgreSQL, scoring, writer, UI) |
| `kafka_worker.py`    | Читает транзакции из Kafka, выполняет препроцессинг и скоринг             |
| `db_writer.py`       | Читает результаты скоринга из Kafka и сохраняет их в PostgreSQL           |
| `app.py`             | Интерфейс на Streamlit для просмотра результатов                          |
| `model.pkl`          | Предобученная модель для скоринга                                         |
| `features.json`      | Список признаков, используемых моделью                                    |
| `threshold.txt`      | Порог для классификации транзакции как fraud                              |
| `requirements.txt`   | Список зависимостей Python                                                |

---

## Запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/Nik-optimase/MLOps-v2.git
cd MLOps-v2
```

### 2. Сборка и запуск контейнеров

```bash
docker-compose up -d
```

После запуска будут подняты сервисы:

* `zookeeper`, `kafka`
* `postgres`
* `scoring-service` (воркер для скоринга)
* `db-writer` (запись результатов в БД)
* `ui` (интерфейс Streamlit)

### 3. Отправка тестового сообщения в Kafka

```bash
docker exec -it kafka bash -lc "kafka-console-producer.sh --broker-list kafka:9092 --topic transactions"
```

Пример сообщения в формате JSON:

```json
{"transaction_id": "t_001", "amount": 1200, "latitude": 55.75, "longitude": 37.62, "hour": 14, "device_type": "mobile"}
```

### 4. Интерфейс

После запуска доступен по адресу:

```
http://localhost:8501
```

Интерфейс позволяет:

* Просматривать последние 10 транзакций с `fraud_flag = 1`
* Строить гистограмму распределения скорингов для последних 100 транзакций

---

## Структура таблицы PostgreSQL

```sql
CREATE TABLE scores (
  transaction_id TEXT PRIMARY KEY,
  score DOUBLE PRECISION,
  fraud_flag INT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Логика работы

1. `kafka_worker.py` считывает транзакции из топика `transactions`.
2. После препроцессинга формируется вектор признаков в порядке, определенном в `features.json`.
3. Модель (`model.pkl`) вычисляет вероятность мошенничества (`score`).
4. Если `score >= threshold.txt`, присваивается `fraud_flag = 1`, иначе `0`.
5. Результаты отправляются в топик `scores` и затем сохраняются в PostgreSQL.
6. `app.py` отображает данные из таблицы `scores` в виде таблицы и гистограммы.

---

## Зависимости

Все необходимые библиотеки указаны в `requirements.txt`:

```
pandas
numpy
catboost
scikit-learn
kafka-python
psycopg2-binary
streamlit
matplotlib
```

---

## Проверка и отладка

Проверить запущенные контейнеры:

```bash
docker ps
```

Посмотреть логи:

```bash
docker logs scoring-service
docker logs db-writer
```

Подключиться к базе данных:

```bash
docker exec -it postgres psql -U mlops -d fraud
SELECT * FROM scores LIMIT 10;
```


