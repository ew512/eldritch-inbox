### FastAPI Connection to Firestore Database for Writing Style References ###

# Import libraries
from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import firestore

app = FastAPI(title="Writing Style References")

# Initialise Firestore client
db = firestore.Client()
collection = db.collection("style_references")

class styleRef(BaseModel):
    author: str
    subgenre: str
    excerpt: str
    source: str

# Root endpoint
@app.get("/")
def root():
    return {"message":"Endpoint is running"}

# GET endpoint - crucial for LLM augmentation
@app.get("/styles")
def get_styles():
    docs = collection.stream()
    logs = []

    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        logs.append(item)
    
    return {"logs":logs}

# POST endpoint
@app.post("/add")
def add_style(style:styleRef):
    style_ref = collection.document()
    style_ref.set(style.model_dump())

    return {
        "status":"success",
        "id": style_ref.id,
        "log":style.model_dump()
    }