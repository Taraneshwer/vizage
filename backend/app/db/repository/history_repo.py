"""
Repository for History management.
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
from app.db.models import RecognitionHistory
from app.db.repository.base_repository import BaseRepository

class HistoryRepository(BaseRepository[RecognitionHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(RecognitionHistory, session)

    async def get_history(self, limit: int, offset: int, search: Optional[str] = None) -> Tuple[List[RecognitionHistory], int]:
        stmt = select(RecognitionHistory)
        
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    RecognitionHistory.name.ilike(search_pattern),
                    RecognitionHistory.identity_id.ilike(search_pattern),
                    RecognitionHistory.department.ilike(search_pattern),
                    RecognitionHistory.tracking_id.ilike(search_pattern),
                    RecognitionHistory.mode.ilike(search_pattern)
                )
            )
            
                         
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
                            
        stmt = stmt.order_by(RecognitionHistory.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        records = list(result.scalars().all())
        
        return records, total
        
    async def clear_all(self):
        stmt = delete(RecognitionHistory)
        await self.session.execute(stmt)
