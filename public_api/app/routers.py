import os
from typing import List
import uuid

from fastapi import FastAPI, APIRouter, Depends, HTTPException, UploadFile, File, Response
from starlette.status import HTTP_204_NO_CONTENT
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

import aiofiles
import httpx

from app import models, schemas, crud, utils
from app.database import get_db
from app.models import Meme


load_dotenv()

router = APIRouter()
PRIV_API_URL = os.getenv('PRIV_API_URL', "http://s3_service:8001")

@router.post("/memes/", response_model=schemas.Meme, status_code=201,)
async def create_meme(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Создание нового мема.
    """
    file_path = await utils.save_temp_file(file)

    response_data = await utils.upload_to_s3(file_path, PRIV_API_URL)

    await utils.delete_temp_file(file_path)

    file_url = response_data["file_url"]
    unique_filename = response_data["file_name"]

    db_meme = await crud.create_meme(
                    db=db, 
                    original_filename=file.filename,
                    unique_filename=unique_filename,
                    image_url=file_url,
                    )

    data = schemas.Meme.model_validate(db_meme)
    data = data.model_dump()

    return data

@router.get("/memes/",response_model=List[schemas.Meme])
async def read_memes(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    # можно реализовать получение мемов так же через с3 хранилище,
    # но это зависит от общих бизнес требований.
    # в данном случае мы возвращаем только те мемы, которые были созданы в публичном апи,
    # чтобы не выводить мемы которые были добавлены через другие сервисы или напрямую через хранилище
    db_memes = await crud.get_memes(db=db, skip=skip, limit=limit)
    data = [schemas.Meme.model_validate(meme) for meme in db_memes]
    return data


@router.get("/memes/{meme_id}", response_model=schemas.Meme)
async def read_meme(meme_id: int, db: AsyncSession = Depends(get_db)):
    meme = await crud.get_meme(db, meme_id=meme_id)
    if meme is None:
        raise HTTPException(status_code=404, detail="Meme not found")
    data = schemas.Meme.model_validate(meme).model_dump()
    return data

#в некоторых s3 хранилищах файл не перезаписывается даже если отправить корректное название файла, поэтому при обновлении его нужно намеренно удалять
@router.put("/memes/{meme_id}", response_model=schemas.Meme)
async def update_meme(meme_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Получаем существующий мем из базы данных
    db_meme = await db.get(models.Meme, meme_id)
    if not db_meme:
        raise HTTPException(status_code=404, detail="Meme not found")

    file_path = await utils.save_temp_file(file)

    try:
        #запрос на удаление
        await utils.delete_from_s3(db_meme.unique_filename, PRIV_API_URL)
        #запрос на создание
        response_data = await utils.upload_to_s3(file_path, PRIV_API_URL)

        file_url = response_data["file_url"]
        unique_filename = response_data["file_name"]

        # Вызываем функцию из crud для обновления записи
        updated_meme = await crud.update_meme(db, meme_id, file_url, file.filename, unique_filename)
        if not updated_meme:
            raise HTTPException(status_code=404, detail="Failed to update meme")

    finally:
        await utils.delete_temp_file(file_path)

    data = schemas.Meme.model_validate(updated_meme)
    data = data.model_dump()

    return data


@router.delete(
    "/memes/{meme_id}",
    status_code=HTTP_204_NO_CONTENT,
    responses={
        404: {
            "description": "Meme not found",
            "content": {"application/json": {"example": {"detail": "Meme not found"}}},
        },
        500: {
            "description": "Failed to delete file from S3",
            "content": {"application/json": {"example": {"detail": "Failed to delete file from S3: {error_message}"}}},
        },
    }
)
async def delete_meme(meme_id: int, db: AsyncSession = Depends(get_db)):
    # Получаем существующий мем из базы данных
    db_meme = await crud.get_meme(db, meme_id)
    if not db_meme:
        raise HTTPException(status_code=404, detail="Meme not found")

    # Удаляем файл с S3
    try:
        response = await utils.delete_from_s3(db_meme.unique_filename, PRIV_API_URL)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to delete file from S3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file from S3: {str(e)}")

    # Удаляем мем из базы данных
    await crud.delete_meme(db, meme_id)

    return Response(status_code=204)