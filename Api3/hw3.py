from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime
from database import init_db, save_file_to_db, get_files_from_db, get_db
from models import FileInfo
from sqlmodel import Session

app = FastAPI()

# Директории для хранения файлов и превью
UPLOAD_FOLDER = Path("files")
PREVIEW_FOLDER = Path("previews")

# Создаем папки, если они не существуют
UPLOAD_FOLDER.mkdir(exist_ok=True)
PREVIEW_FOLDER.mkdir(exist_ok=True)

# Инициализация базы данных при запуске
init_db()

# Генерация уникального ID
def generate_file_id():
    return str(uuid.uuid4())

# Генерация превью для изображений
def generate_image_preview(file_path, preview_path, width, height):
    img = Image.open(file_path)
    img.thumbnail((width, height))
    img.save(preview_path, "JPEG")

# Генерация превью для видео
def generate_video_preview(file_path, preview_path, width, height):
    clip = VideoFileClip(str(file_path))
    frame = clip.get_frame(0)  # Получаем первый кадр
    clip.close()

    img = Image.fromarray(frame)
    img.thumbnail((width, height))
    img.save(preview_path, "JPEG")

@app.put("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_id = generate_file_id()
    file_extension = os.path.splitext(file.filename)[1]
    file_path = UPLOAD_FOLDER / f"{file_id}{file_extension}"

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Получаем размер файла
    file_size = len(content)

    # Определяем тип файла (IMG или VID)
    file_type = "IMG" if file_extension.lower() in [".jpg", ".jpeg", ".png", ".gif"] else "VID"

    # Записываем информацию о файле в базу данных
    save_file_to_db(file_id, file_type, file_size, str(file_path))

    return {"file_id": file_id, "filename": file.filename}

@app.get("/download/{file_id}")
async def download_file(file_id: str, width: Optional[int] = Query(None), height: Optional[int] = Query(None), db: Session = Depends(get_db)):
    # Получаем информацию о файле из базы данных
    files = get_files_from_db()
    file_info = next((file for file in files if file["id"] == file_id), None)

    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(file_info["file_path"])
    file_extension = os.path.splitext(file_path.name)[1].lower()

    # Если запрошено превью
    if width is not None and height is not None:
        preview_path = PREVIEW_FOLDER / f"{file_id}_{width}x{height}.jpg"
        if not preview_path.exists():
            try:
                if file_extension in [".jpg", ".jpeg", ".png", ".gif"]:
                    generate_image_preview(file_path, preview_path, width, height)
                elif file_extension in [".mp4", ".avi", ".mov"]:
                    generate_video_preview(file_path, preview_path, width, height)
                else:
                    raise HTTPException(status_code=400, detail="File format not supported for preview")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

        return FileResponse(preview_path, media_type="image/jpeg")

    return FileResponse(file_path, filename=file_info["file_path"])

@app.get("/files/")
def list_files(db: Session = Depends(get_db)):
    # Получаем все файлы из базы данных
    files = get_files_from_db()

    # Возвращаем всю информацию о файлах
    return {
        "files": [
            {
                "id": file["id"],
                "file_type": file["file_type"],
                "file_size": file["file_size"],
                "file_path": file["file_path"],
                "upload_time": file["upload_time"],
            }
            for file in files
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)