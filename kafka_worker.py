import os
import json
import pandas as pd
import numpy as np
from kafka import KafkaConsumer, KafkaProducer
import pickle

# Load model and artifacts
model_path = os.getenv("MODEL_PATH", "model.pkl")
features_path = os.getenv("FEATURES_JSON", "features.json")
medians_path = os.getenv("MEDIANS_JSON", "medians.json")
rare_maps_path = os.getenv("RARE_MAPS_JSON", "rare_maps.json")
threshold_path = os.getenv("THRESHOLD_PATH", "threshold.txt")

with open(features_path, "r") as f:
    features = json.load(f)

with open(model_path, "rb") as f:
    model = pickle.load(f)

# Load medians and rare_maps if available
if os.path.isfile(medians_path):
    with open(medians_path, "r") as f:
        medians = json.load(f)
else:
    medians = {}

if os.path.isfile(rare_maps_path):
    with open(rare_maps_path, "r") as f:
        rare_maps = json.load(f)
else:
    rare_maps = {}

# Load threshold
threshold = 0.5
try:
    with open(threshold_path, "r") as f:
        threshold = float(f.read().strip())
except Exception:
    pass

def preprocess_record(rec):
    """Preprocess a single transaction record into feature vector."""
    df = pd.DataFrame([rec])
    # Convert numeric columns
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass
    # Fill missing values with medians
    for col, med in medians.items():
        if col in df.columns:
            df[col] = df[col].fillna(med)
    # Rare value mapping
    for col, mapping in rare_maps.items():
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: mapping.get(x, x))
    # Reorder columns
    df = df.reindex(columns=features, fill_value=np.nan)
    return df

def score_transaction(rec):
    df = preprocess_record(rec)
    if hasattr(model, "predict_proba"):
        prob = model.predict_proba(df)[0][1]
    else:
        prob = model.predict(df)[0]
    fraud_flag = 1 if prob >= threshold else 0
    return float(prob), int(fraud_flag)

def main():
    input_topic = os.environ.get("INPUT_TOPIC", "transactions")
    output_topic = os.environ.get("OUTPUT_TOPIC", "scores")
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    consumer = KafkaConsumer(
        input_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="mlops_scoring_group",
    )
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    for msg in consumer:
        rec = msg.value
        transaction_id = rec.get("transaction_id")
        score, flag = score_transaction(rec)
        result = {
            "transaction_id": transaction_id,
            "score": score,
            "fraud_flag": flag,
        }
        producer.send(output_topic, result)
        producer.flush()

if __name__ == "__main__":
    main()
