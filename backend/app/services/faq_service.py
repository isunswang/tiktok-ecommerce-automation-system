"""FAQ service for knowledge base management."""

import logging
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import FAQ, FAQCategory, FAQStatus

logger = logging.getLogger(__name__)


class FAQService:
    """Service for FAQ knowledge base management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_faq(
        self,
        query: str,
        category: Optional[FAQCategory] = None,
        language: str = "en",
        limit: int = 5
    ) -> list[FAQ]:
        """
        搜索FAQ
        
        Args:
            query: 搜索关键词
            category: 分类过滤
            language: 语言
            limit: 返回数量限制
            
        Returns:
            FAQ列表
        """
        # 构建查询
        stmt = select(FAQ).where(FAQ.status == FAQStatus.ACTIVE)
        
        if category:
            stmt = stmt.where(FAQ.category == category)
        
        # 关键词搜索
        if query:
            # 精确匹配
            stmt = stmt.where(
                or_(
                    FAQ.question.contains(query),
                    FAQ.question_en.contains(query),
                    FAQ.keywords.contains([query])
                )
            )
        
        # 按优先级和查看次数排序
        stmt = stmt.order_by(FAQ.priority.desc(), FAQ.view_count.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_faq_by_id(self, faq_id: str) -> Optional[FAQ]:
        """根据ID获取FAQ"""
        stmt = select(FAQ).where(FAQ.id == faq_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_faq_by_category(
        self,
        category: FAQCategory,
        limit: int = 10
    ) -> list[FAQ]:
        """根据分类获取FAQ列表"""
        stmt = select(FAQ).where(
            FAQ.category == category,
            FAQ.status == FAQStatus.ACTIVE
        ).order_by(FAQ.priority.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_faq(
        self,
        category: str,
        question: str,
        answer: str,
        question_en: Optional[str] = None,
        answer_en: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        match_rules: Optional[dict] = None,
        **kwargs
    ) -> FAQ:
        """创建FAQ"""
        faq = FAQ(
            category=category,
            question=question,
            answer=answer,
            question_en=question_en,
            answer_en=answer_en,
            keywords=keywords,
            match_rules=match_rules,
            **kwargs
        )
        
        self.db.add(faq)
        await self.db.commit()
        await self.db.refresh(faq)
        
        logger.info(f"Created FAQ: {faq.id}")
        return faq

    async def update_faq(
        self,
        faq_id: str,
        **kwargs
    ) -> Optional[FAQ]:
        """更新FAQ"""
        stmt = select(FAQ).where(FAQ.id == faq_id)
        result = await self.db.execute(stmt)
        faq = result.scalar_one_or_none()
        
        if not faq:
            logger.error(f"FAQ {faq_id} not found")
            return None

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(faq, key):
                setattr(faq, key, value)
        
        await self.db.commit()
        await self.db.refresh(faq)
        
        logger.info(f"Updated FAQ: {faq_id}")
        return faq

    async def increment_view_count(self, faq_id: str) -> None:
        """增加查看次数"""
        stmt = select(FAQ).where(FAQ.id == faq_id)
        result = await self.db.execute(stmt)
        faq = result.scalar_one_or_none()
        
        if faq:
            faq.view_count += 1
            await self.db.commit()

    async def increment_helpful_count(self, faq_id: str) -> None:
        """增加有用次数"""
        stmt = select(FAQ).where(FAQ.id == faq_id)
        result = await self.db.execute(stmt)
        faq = result.scalar_one_or_none()
        
        if faq:
            faq.helpful_count += 1
            await self.db.commit()

    async def match_faq_by_rules(
        self,
        message: str,
        category: Optional[str] = None
    ) -> Optional[FAQ]:
        """
        根据匹配规则匹配FAQ
        
        Args:
            message: 用户消息
            category: 分类限制
            
        Returns:
            匹配的FAQ,未找到返回None
        """
        # 获取所有活跃FAQ
        stmt = select(FAQ).where(FAQ.status == FAQStatus.ACTIVE)
        
        if category:
            stmt = stmt.where(FAQ.category == category)
        
        result = await self.db.execute(stmt)
        faqs = result.scalars().all()

        # 遍历匹配规则
        for faq in faqs:
            if not faq.match_rules:
                continue

            # 精确匹配
            exact_matches = faq.match_rules.get("exact_match", [])
            if message in exact_matches:
                return faq

            # 模糊匹配
            fuzzy_matches = faq.match_rules.get("fuzzy_match", [])
            for fuzzy in fuzzy_matches:
                if fuzzy in message:
                    return faq

            # 正则匹配
            import re
            regex_patterns = faq.match_rules.get("regex", [])
            for pattern in regex_patterns:
                if re.search(pattern, message):
                    return faq

        return None

    async def get_popular_faqs(self, limit: int = 10) -> list[FAQ]:
        """获取热门FAQ"""
        stmt = select(FAQ).where(
            FAQ.status == FAQStatus.ACTIVE
        ).order_by(FAQ.view_count.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
