### Main HTML-supported Frontend with Form Submission ###

# Import libraries
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from google.cloud import firestore
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
import os
import httpx
import hmac
import hashlib

# Get n8n webhook url from env
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# Initialise Firestore database
db = firestore.Client()

# Hash function for email
def hash_email(email:str) -> str:
    email_secret = os.getenv("EMAIL_HASH_SECRET")
    if not email_secret:
        raise RuntimeError("EMAIL_HASH_SECRET not set")
    else:
        return hmac.new(
            email_secret.encode(),
            email.encode(),
            hashlib.sha256
        ).hexdigest()

# Get IP address function for deployed app
def get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host

# Initialise app
app = FastAPI(title="Eldritch Inbox")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST", "GET"])

# Initialise limiter
limiter = Limiter(key_func=get_real_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files for HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

# Establish input validators
""" Input validation code modified from GitHub
    https://gist.github.com/amahi2001/0c0835f97764460ead630169b2ba51ae """

class UploadForm(BaseModel):
    email: Optional[EmailStr] = None

async def validate_image_file(file:UploadFile) -> bool:
    if file.content_type not in ["image/jpeg", "image/png","image/heic"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Please upload only JPEG, PNG or HEIC files."
        )
    
    MAX_FILE_SIZE = 2.5*1024*1024 # 2.5MB size limit to avoid n8n memory overload

    await file.seek(0)

    file_size = 0
    while chunk := await file.read(8192):  # Read in 8KB chunks
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Please upload an image smaller than 2.5 MB."
            )
    
    # Reset file position for later use
    await file.seek(0)
    return True

# Home endpoint
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

# Image submission endpoint
@app.post("/submit")
@limiter.limit("5/minute")
async def submit_image(
    request: Request,
    email: Optional[str] = Form(None),
    setting_image: UploadFile = File(...) ,
    perspective: str = Form("third"),
    tense: str = Form("past"),
    subgenre: str = Form("supernatural")
):

    email_to_validate = email if email and email.strip() else None
    # n8n handles email hashing here as need both hashed and unhashed email

    try:
        form_data = UploadForm(email=email_to_validate)
    except Exception:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    
    await validate_image_file(setting_image)

    image_content = await setting_image.read()

    # Connecting to n8n webhook 
    async with httpx.AsyncClient() as client:
        try:
            # Prepare the file and data payload
            files = {"image": (setting_image.filename, image_content, setting_image.content_type)}
            data = {"email": form_data.email,
                    "perspective": perspective,
                    "tense": tense,
                    "subgenre":subgenre}

            response = await client.post(N8N_WEBHOOK_URL, files=files, data=data, timeout=60.0)
            response.raise_for_status()
            
            result = response.json()

            if result.get("status") == "invalid_image":
                raise HTTPException(status_code=422, detail=result.get("detail", "Invalid image."))
            else:
                return {
                    "status": "success",
                    "prompt": result.get("prompt", "No prompt generated"),
                    "extract": result.get("extract", "No subject generated")
                }
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="The system took too long to respond.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# History page endpoint
@app.get("/history")
async def serve_history():
    return FileResponse("static/history.html")

# Submit email to get history
@app.post("/history")
@limiter.limit("10/minute")
async def get_history(
    request: Request,
    email:EmailStr=Form(...)):
    # Validate email
    try:
        UploadForm(email=email)
    except Exception:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    
    # Hash email
    email_hash = hash_email(str(email).strip())

    # Fetch history from Firestore
    docs = db.collection("eldritch_inbox").where(filter=firestore.FieldFilter("email", "==", email_hash)).order_by("date_time", direction=firestore.Query.DESCENDING).stream()

    entries = []
    for doc in docs:
        data = doc.to_dict()
        entries.append({
            "timestamp": data.get("date_time"),
            "prompt": data.get("prompt"),
            "extract": data.get("extract")
        })

    return {"entries": entries}