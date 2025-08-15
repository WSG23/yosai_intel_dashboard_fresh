import json
import os
from fastapi import FastAPI
from kafka import KafkaProducer

brokers = os.environ.get("KAFKA_BROKERS", "localhost:9092")
producer = KafkaProducer(
    bootstrap_servers=brokers,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

app = FastAPI()

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/api/v1/events")
async def ingest_event(event: dict) -> dict:
    producer.send("access-events", event)
    producer.flush()
    return {"status": "ok"}
