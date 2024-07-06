#пока сервис небольшой, не будем бить его на роуты модели и схемы, а напишем все в main.py
from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
import os
import aiofiles
from app.async_s3_client import AsyncS3Client
from dotenv import load_dotenv
from typing import List, Optional


load_dotenv()

S3_PUBLIC_DOMAIN = os.getenv('S3_PUBLIC_DOMAIN')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_REGION_NAME = os.getenv('S3_REGION_NAME')

app = FastAPI()

# Конфигурация S3 клиента
s3_client = AsyncS3Client(
    endpoint_url=S3_ENDPOINT_URL,
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    bucket_name=S3_BUCKET_NAME,
    # region_name=S3_REGION_NAME,
)

class FileResponse(BaseModel):
    file_name: str
    file_url: str

@app.post("/upload/", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...)):
    object_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"/tmp/{object_name}"

    # Сохраняем временно файл для загрузки
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)

    # Загружаем файл на S3
    # обработка ошибок находится в функции upload_file
    # как вариант, можно еще подключить celery с rmq для фоновой загрузки файла в хранилище
    await s3_client.upload_file(file_path, object_name)

    # Удаляем временный файл
    os.remove(file_path)

    file_url = f"{S3_PUBLIC_DOMAIN}/{object_name}"

    return FileResponse(file_name=object_name, file_url=file_url)

@app.delete("/delete/{file_name}")
async def delete_file(file_name: str):
    result = await s3_client.delete_file(file_name)
    if result["status"] == "success":
        return JSONResponse(status_code=200, content={"message": result["message"]})
    else:
        return JSONResponse(status_code=400, content={"message": result["message"]})