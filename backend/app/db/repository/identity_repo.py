"""
Repository for Identity management.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Identity
from app.db.repository.base_repository import BaseRepository

class IdentityRepository(BaseRepository[Identity]):
    def __init__(self, session: AsyncSession):
        super().__init__(Identity, session)

    async def get_by_identity_id(self, identity_id: str) -> Optional[Identity]:
        stmt = select(Identity).where(Identity.identity_id == identity_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_identities(self) -> List[Identity]:
        stmt = select(Identity).order_by(Identity.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
