### Main HTML-supported Frontend with Form Submission ###

# Import libraries
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import httpx

# Get n8n webhook url from env
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# Initialise app
app = FastAPI(title="Eldritch Inbox")

# Mount static files for HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

""" Input validation code modified from GitHub
    https://gist.github.com/amahi2001/0c0835f97764460ead630169b2ba51ae """

# Establish input validators
class UploadForm(BaseModel):
    email: Optional[EmailStr] = None

async def validate_image_file(file:UploadFile) -> bool:
    if file.content_type not in ["image/jpeg", "image/png","image/heic"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Please upload only JPEG, PNG or HEIC files."
        )
    
    MAX_FILE_SIZE = 2.5*1024*1024

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
async def submit_image(
    email: Optional[str] = Form(None),
    setting_image: UploadFile = File(...) 
):

    email_to_validate = email if email and email.strip() else None

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
            data = {"email": form_data.email}

            response = await client.post(N8N_WEBHOOK_URL, files=files, data=data, timeout=60.0)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "status": "success",
                "prompt": result.get("prompt", "No prompt generated"),
                "extract": result.get("extract", "No subject generated")
            }
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="The system took too long to respond.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"n8n error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")