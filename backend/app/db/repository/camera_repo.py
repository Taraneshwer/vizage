from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models import CameraSource
from typing import List, Optional

class CameraRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[CameraSource]:
        stmt = select(CameraSource).order_by(CameraSource.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, id: str) -> Optional[CameraSource]:
        stmt = select(CameraSource).where(CameraSource.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_active(self) -> Optional[CameraSource]:
        stmt = select(CameraSource).where(CameraSource.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, camera: CameraSource):
        self.session.add(camera)

    async def set_active(self, camera_id: str):
                          
        await self.session.execute(
            update(CameraSource).values(is_active=False)
        )
                           
        if camera_id:
            await self.session.execute(
                update(CameraSource).where(CameraSource.id == camera_id).values(is_active=True)
            )

    async def delete(self, camera: CameraSource):
        await self.session.delete(camera)
