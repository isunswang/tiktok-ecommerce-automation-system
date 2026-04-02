"""Conversation management service for multi-turn dialog."""

import logging
from enum import StrEnum
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_service import CSSession, CSMessage, CSMessageRole, CSSessionStatus

logger = logging.getLogger(__name__)


class ConversationState(StrEnum):
    """对话状态机."""
    START = "start"  # 开始
    INTENT_DETECTED = "intent_detected"  # 已识别意图
    ENTITY_EXTRACTED = "entity_extracted"  # 已提取实体
    ANSWER_GENERATED = "answer_generated"  # 已生成答案
    CONFIRMED = "confirmed"  # 已确认
    END = "end"  # 结束


class ConversationManager:
    """Multi-turn conversation manager."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        buyer_id: str,
        buyer_name: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> CSSession:
        """创建会话"""
        session = CSSession(
            buyer_id=buyer_id,
            buyer_name=buyer_name,
            order_id=order_id,
            status=CSSessionStatus.ACTIVE,
            ai_resolved=False
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Created CS session: {session.id}")
        return session

    async def add_message(
        self,
        session_id: str,
        role: CSMessageRole,
        content: str
    ) -> CSMessage:
        """添加消息"""
        message = CSMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message

    async def get_session(self, session_id: str) -> Optional[CSSession]:
        """获取会话"""
        stmt = select(CSSession).where(CSSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 20
    ) -> list[CSMessage]:
        """获取会话消息历史"""
        stmt = select(CSMessage).where(
            CSMessage.session_id == session_id
        ).order_by(CSMessage.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        
        # 按时间正序排列
        return list(reversed(messages))

    async def update_session_state(
        self,
        session_id: str,
        state: ConversationState,
        context: Optional[dict] = None
    ) -> Optional[CSSession]:
        """
        更新会话状态
        
        Args:
            session_id: 会话ID
            state: 新状态
            context: 上下文数据
            
        Returns:
            更新后的会话
        """
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return None

        # TODO: 将状态存储到session的某个字段中
        # 当前模型没有state字段,可以考虑添加或使用JSONB字段
        
        logger.info(f"Session {session_id} state updated to {state}")
        return session

    async def end_session(self, session_id: str, ai_resolved: bool = True) -> Optional[CSSession]:
        """结束会话"""
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return None

        session.status = CSSessionStatus.CLOSED
        session.ai_resolved = ai_resolved
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Session {session_id} ended, ai_resolved={ai_resolved}")
        return session

    async def escalate_to_human(self, session_id: str, reason: str) -> Optional[CSSession]:
        """转人工"""
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return None

        session.status = CSSessionStatus.ESCALATED
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Session {session_id} escalated to human: {reason}")
        return session

    async def get_conversation_context(
        self,
        session_id: str
    ) -> dict:
        """
        获取对话上下文
        
        Returns:
            {
                "messages": list[dict],
                "intent": str,
                "entities": dict,
                "state": str
            }
        """
        messages = await self.get_session_messages(session_id)
        
        # 转换为字典列表
        message_list = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
        
        return {
            "messages": message_list,
            "intent": None,  # TODO: 从会话状态中获取
            "entities": {},  # TODO: 从会话状态中获取
            "state": ConversationState.START  # TODO: 从会话状态中获取
        }

    async def should_continue_conversation(
        self,
        session_id: str
    ) -> bool:
        """
        判断是否应该继续对话
        
        检查:
        1. 会话是否已关闭
        2. 是否超过最大轮次
        3. 是否需要转人工
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        # 检查会话状态
        if session.status in [CSSessionStatus.CLOSED, CSSessionStatus.ESCALATED]:
            return False

        # 检查消息轮次
        messages = await self.get_session_messages(session_id, limit=100)
        if len(messages) >= 50:  # 最多50轮对话
            logger.warning(f"Session {session_id} exceeded max conversation turns")
            return False

        return True

    async def get_active_sessions(self, limit: int = 50) -> list[CSSession]:
        """获取活跃会话"""
        stmt = select(CSSession).where(
            CSSession.status == CSSessionStatus.ACTIVE
        ).order_by(CSSession.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        清理旧会话
        
        Args:
            days: 清理多少天前的会话
            
        Returns:
            清理的数量
        """
        from datetime import datetime, timedelta
        
        threshold = datetime.utcnow() - timedelta(days=days)
        
        # TODO: 实现清理逻辑
        # 注意: 需要级联删除消息或归档
        
        logger.info(f"Cleaned up sessions older than {days} days")
        return 0
