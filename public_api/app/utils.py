from fastapi import UploadFile, HTTPException
import httpx
import os
import uuid
import logging


async def save_temp_file(file: UploadFile) -> str:
    object_name = file.filename
    file_path = f"/tmp/{object_name}"

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return file_path

async def upload_file_to_s3(file_path: str, api_url: str, endpoint: str) -> dict:
    """
    Универсальная функция для загрузки файла и обновления на указанный endpoint.
    """
    # можно использовать как celery таску с rmq как брокером, но это бы выходило уже из рамок тестового задания
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(file_path, "rb") as file_obj:
            response = await client.post(
                f"{api_url}/{endpoint}",
                files={"file": file_obj}
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to upload file")

        return response.json()

async def upload_to_s3(file_path: str, PRIV_API_URL) -> dict:
    return await upload_file_to_s3(file_path, PRIV_API_URL, 'upload/')

async def delete_temp_file(file_path: str):
    try:
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Error deleting temporary file: {e}")

async def delete_from_s3(unique_filename: str, PRIV_API_URL):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{PRIV_API_URL}/delete/{unique_filename}")
        return response