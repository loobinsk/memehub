#с тестами особо не заморачивался, занимает много времени. Можно было написать намного больше и сделать тестирование более детальнее и качественнее 
import pytest
from httpx import AsyncClient, ASGITransport, Response
from app.models import Meme
from app import utils


s3_mock_data = {'file_url': 'https://somedomen/file_path', 'file_name': 'uudi_test.png'}

async def test_create_meme(client: AsyncClient, mocker):
    #мокаем работу с с3 хранилищем, т.к unit тесты должны быть изолированными и не быть зависимыми от внешних сервисов
    mocker.patch('app.utils.upload_to_s3', return_value=s3_mock_data)

    file_path = "static/test.png"
    file_content = b"test content"
    files = {"file": ("test.png", file_content, "image/png")}
    response = await client.post(
        "/memes/",
        files=files
    )
    json_response = response.json()

    assert response.status_code == 201
    assert json_response["original_filename"] == "test.png"
    assert s3_mock_data['file_name'] == json_response["unique_filename"]
    assert s3_mock_data['file_url'] == json_response["image_url"]

async def test_get_meme_by_id(client: AsyncClient):
    meme_id = 1
    response = await client.get(f"/memes/{meme_id}")
    json_response = response.json()

    assert response.status_code == 200
    assert json_response["original_filename"] == "test.png"
    assert s3_mock_data['file_name'] == json_response["unique_filename"]
    assert s3_mock_data['file_url'] == json_response["image_url"]
    assert 1 == json_response["id"]

async def test_read_memes(client: AsyncClient):
    skip = 0
    limit = 2

    response = await client.get(f"/memes/?skip={skip}&limit={limit}")
    json_response = response.json()

    assert response.status_code == 200
    assert len(json_response) == 1
    i = 0
    assert json_response[i]["original_filename"] == "test.png"
    assert json_response[i]["unique_filename"] == s3_mock_data['file_name']
    assert json_response[i]["image_url"] == s3_mock_data['file_url']
    assert json_response[i]["id"] == 1

async def test_delete_meme(client: AsyncClient, mocker):
    mocker.patch('app.utils.delete_from_s3', return_value=Response(status_code=200))
    meme_id = 1

    response = await client.delete(f"/memes/{meme_id}")

    assert response.status_code == 204
    memes_response = await client.get(f"/memes/?skip={0}&limit={10}")
    memes_json_response = memes_response.json()
    assert len(memes_json_response) == 0 

