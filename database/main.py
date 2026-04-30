# Import libraries
import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import firestore

app = FastAPI(title="Eldritch Inbox Log")

# Initialise Firestore client
db = firestore.Client()
collection = db.collection("eldritch_inbox")

class LogEntry(BaseModel):
    email: str | None = None
    date_time: datetime.datetime
    prompt: str
    extract: str

@app.get("/")
def root():
    return {"message": "Eldritch Inbox Log is running."}

@app.get("/logs")
def get_logs():
    docs = collection.stream()
    logs = []

    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        logs.append(item)
    
    return {"logs":logs}

@app.post("/add")
def add_log(log:LogEntry):
    log_ref = collection.document()
    log_ref.set(log.model_dump())

    return {
        "status":"success",
        "id": log_ref.id,
        "log":log.model_dump()
    }