from datetime import datetime, timezone
import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from peachcheck.pipeline import run_pipeline
from PIL import Image, ExifTags

app = FastAPI(title="PeachCheck Walking Skeleton API")

# Allow UI to connect later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_exif(file_path: str) -> dict:
    """Helper to extract EXIF data to fulfill the Phase 1 EXIF requirement."""
    exif_data = {}
    try:
        with Image.open(file_path) as img:
            raw_exif = img.getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)
    except Exception:
        pass
    return exif_data

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
        
    # Save uploaded file to a temporary file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    analyzed_at_iso = datetime.now(timezone.utc).isoformat()
    mime_type = file.content_type or "application/octet-stream"
    
    # 1. Get EXIF (Week 1 explicit requirement)
    exif = extract_exif(file_path)
    
    # 2. Run the main pipeline (which runs the Provenance layer we just built)
    try:
        report = run_pipeline(file_path, mime_type, analyzed_at_iso)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)
        
    # Return both the EXIF (for the walking skeleton requirement) and the pipeline report
    return {
        "exif_data": exif,
        "trust_report": report
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
