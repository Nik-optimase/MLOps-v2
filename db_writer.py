import os, json, psycopg2
from kafka import KafkaConsumer

# --- Postgres ---
conn = psycopg2.connect(
    host=os.getenv("PGHOST", "postgres"),
    port=os.getenv("PGPORT", "5432"),
    dbname=os.getenv("PGDATABASE", "fraud"),
    user=os.getenv("PGUSER", "mlops"),
    password=os.getenv("PGPASSWORD", "mlops"),
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS scores(
  transaction_id TEXT PRIMARY KEY,
  score DOUBLE PRECISION,
  fraud_flag INT,
  created_at TIMESTAMP DEFAULT NOW()
)""")

# --- Kafka consumer ---
consumer = KafkaConsumer(
    os.getenv("SCORES_TOPIC", "scores"),
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    enable_auto_commit=True,
    auto_offset_reset="earliest",
)

for msg in consumer:
    v = msg.value
    cur.execute(
        "INSERT INTO scores(transaction_id, score, fraud_flag) "
        "VALUES (%s, %s, %s) ON CONFLICT (transaction_id) DO NOTHING",
        (str(v["transaction_id"]), float(v["score"]), int(v["fraud_flag"]))
    )
