### Main HTML-supported Frontend with Form Submission ###

# Import libraries
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from datetime import datetime

# Initialise app
app = FastAPI(title="Eldritch Inbox")

# Mount static files for HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

""" Input validation code modified from GitHub
    https://gist.github.com/amahi2001/0c0835f97764460ead630169b2ba51ae """

# Establish input validators
class UploadForm(BaseModel):
    email: EmailStr

async def validate_image_file(file:UploadFile) -> bool:
    if file.content_type not in ["image/jpeg", "image/png","image/heic"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Please upload only JPEG, PNG or HEIC files."
        )
    
    MAX_FILE_SIZE = 2*1024*1024

    await file.seek(0)

    file_size = 0
    while chunk := await file.read(8192):  # Read in 8KB chunks
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Please upload an image smaller than 2MB."
            )
    
    # Reset file position for later use
    await file.seek(0)
    return True

# Home endpoint
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

# Image submission endpoint
@app.post("/submit/")
async def submit_image(
    email: Optional[EmailStr] = Form(...),
    setting_image: UploadFile = File(...) 
):
    try:
        form_data = UploadForm(email=email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    await validate_image_file(setting_image)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    setting_image_filename = f"{timestamp}_{setting_image.filename}"
    setting_image_path = os.path.join("uploads",setting_image_filename)

    with open(setting_image_path, "wb") as f:
            content = await setting_image.read()
            f.write(content)
    
    return {
        "email": form_data.model_dump(),
        "setting_image_path": setting_image_path
    }