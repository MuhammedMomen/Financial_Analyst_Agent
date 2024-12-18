import flet as ft
import os
from ui import main as ui_main
from config.app_config import flet_secret_key
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import uuid
import time
from pathlib import Path
import threading
import uvicorn

# Create directories if they don't exist
UPLOAD_DIR = Path("upload_dir")
OUTPUT_DIR = Path("output") # to store the temp file from download links.

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI()

# Mount the upload directory and output directory for static file serving
app.mount("/upload_dir", StaticFiles(directory="upload_dir"), name="upload_dir")
app.mount("/output", StaticFiles(directory="output"), name="output")


@app.get("/download/{filename}")
async def download(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return {"error": "File not found"}
    
    # Set headers to force download dialog
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf',
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


if __name__ == "__main__":
    # Set FLET_SECRET_KEY as environment variable
    os.environ["FLET_SECRET_KEY"] = flet_secret_key
    
    # Run FastAPI server in a separate thread
    threading.Thread(
        target=lambda: uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8001
        ),
        daemon=True
    ).start()
    
    ft.app(target=ui_main.main, view=ft.AppView.WEB_BROWSER, assets_dir="assets", upload_dir=str(UPLOAD_DIR), port=8550)