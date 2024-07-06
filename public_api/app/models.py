from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Meme(Base):
    __tablename__ = "memes"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False) # имя файла без UUID 
    unique_filename = Column(String, nullable=False) # уникальное имя файла uuid для обращения к с3 хранилищу
    description = Column(Text, nullable=True) # на всякий
    image_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)