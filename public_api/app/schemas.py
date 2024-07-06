from pydantic import BaseModel
from sqlalchemy_to_pydantic import sqlalchemy_to_pydantic
from app.models import Meme
from typing import List


PydanticMeme = sqlalchemy_to_pydantic(Meme)

class Meme(PydanticMeme):
    pass

class MemesOut(BaseModel):
    memes: List[Meme]