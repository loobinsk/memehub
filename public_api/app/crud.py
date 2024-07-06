from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas


async def get_meme(db: AsyncSession, meme_id: int):
    result = await db.execute(select(models.Meme).filter(models.Meme.id == meme_id))
    return result.scalars().first()

async def get_memes(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(models.Meme).offset(skip).limit(limit))
    return result.scalars().all()

async def create_meme(db: AsyncSession, original_filename: str, 
                                        unique_filename: str, 
                                        image_url: str, 
                                        description: str = None
                                        ):
    db_meme = models.Meme(
        original_filename=original_filename,
        unique_filename=unique_filename,
        description=description,
        image_url=image_url,
    )
    db.add(db_meme)
    await db.commit()
    await db.refresh(db_meme)
    return db_meme

async def delete_meme(db: AsyncSession, meme_id: int):
    result = await db.execute(select(models.Meme).filter(models.Meme.id == meme_id))
    meme = result.scalars().first()
    if meme:
        await db.delete(meme)
        await db.commit()
        return meme
    return None


async def update_meme(db: AsyncSession, meme_id: int, file_url: str, original_filename: str, unique_filename: str):
    db_meme = await db.get(models.Meme, meme_id)
    if not db_meme:
        return None
    
    db_meme.image_url = file_url
    db_meme.original_filename = original_filename
    db_meme.unique_filename = unique_filename
    
    await db.commit()
    await db.refresh(db_meme)
    
    return db_meme