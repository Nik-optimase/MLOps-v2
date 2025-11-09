import os, psycopg2, pandas as pd, matplotlib.pyplot as plt, streamlit as st

conn = psycopg2.connect(
    host=os.getenv("PGHOST", "postgres"),
    port=os.getenv("PGPORT", "5432"),
    dbname=os.getenv("PGDATABASE", "fraud"),
    user=os.getenv("PGUSER", "mlops"),
    password=os.getenv("PGPASSWORD", "mlops"),
)

st.title("Fraud Scores Dashboard")

if st.button("Посмотреть результаты"):
    df = pd.read_sql(
        "SELECT transaction_id, score, fraud_flag, created_at "
        "FROM scores WHERE fraud_flag=1 ORDER BY created_at DESC LIMIT 10",
        conn,
    )
    st.subheader("Последние 10 fraud_flag=1")
    st.dataframe(df)

    df100 = pd.read_sql(
        "SELECT score FROM scores ORDER BY created_at DESC LIMIT 100", conn
    )
    st.subheader("Гистограмма скоров (последние 100)")
    fig, ax = plt.subplots()
    ax.hist(df100["score"].astype(float), bins=20)
    st.pyplot(fig)
