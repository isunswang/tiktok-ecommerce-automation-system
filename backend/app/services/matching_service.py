"""SKU matching service for order fulfillment."""

import asyncio
import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.mapping import SKUMapping, MatchRecord, MatchMethod
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductSku
from app.services.tiktok_service import TikTokShopService

logger = logging.getLogger(__name__)


class MatchingService:
    """SKU matching engine for order fulfillment."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tiktok_service = TikTokShopService()
        
        # 匹配阈值配置
        self.NAME_SIMILARITY_THRESHOLD = getattr(settings, 'NAME_SIMILARITY_THRESHOLD', 0.7)
        self.IMAGE_SIMILARITY_THRESHOLD = getattr(settings, 'IMAGE_SIMILARITY_THRESHOLD', 0.8)
        self.CONFIDENCE_THRESHOLD = getattr(settings, 'CONFIDENCE_THRESHOLD', 0.75)

    async def match_order_items(self, order_id: str) -> list[MatchRecord]:
        """
        匹配订单中的所有商品项
        
        Args:
            order_id: 订单ID
            
        Returns:
            匹配记录列表
        """
        # 获取订单及其商品项
        order = await self._get_order_with_items(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return []

        match_records = []
        for item in order.items:
            try:
                record = await self._match_single_item(item)
                match_records.append(record)
            except Exception as e:
                logger.error(f"Failed to match item {item.id}: {e}", exc_info=True)
                # 创建失败记录
                record = MatchRecord(
                    order_id=order.id,
                    order_item_id=item.id,
                    match_method=MatchMethod.MANUAL,
                    is_matched=False,
                    failure_reason=str(e)
                )
                self.db.add(record)
        
        await self.db.commit()
        return match_records

    async def _match_single_item(self, item: OrderItem) -> MatchRecord:
        """
        匹配单个订单项
        
        策略优先级:
        1. SKU编码精确匹配
        2. 名称相似度 + 图片相似度综合匹配
        3. 规格匹配
        """
        # 尝试SKU编码匹配
        if item.sku_code:
            mapping = await self._match_by_sku_code(item.sku_code)
            if mapping:
                return self._create_match_record(
                    item, mapping, MatchMethod.SKU_CODE, 1.0
                )

        # 尝试名称和图片匹配
        name_mapping, name_score = await self._match_by_name_similarity(item)
        image_mapping, image_score = await self._match_by_image_similarity(item)
        
        # 综合评分
        if name_mapping and image_mapping and name_mapping.id == image_mapping.id:
            combined_score = (name_score + image_score) / 2
            if combined_score >= self.CONFIDENCE_THRESHOLD:
                return self._create_match_record(
                    item, name_mapping, MatchMethod.NAME_SIMILARITY, combined_score
                )
        
        # 选择最高分的匹配
        best_mapping = None
        best_score = 0.0
        best_method = MatchMethod.MANUAL
        
        if name_mapping and name_score > best_score:
            best_mapping = name_mapping
            best_score = name_score
            best_method = MatchMethod.NAME_SIMILARITY
        
        if image_mapping and image_score > best_score:
            best_mapping = image_mapping
            best_score = image_score
            best_method = MatchMethod.IMAGE_SIMILARITY
        
        if best_mapping and best_score >= self.CONFIDENCE_THRESHOLD:
            return self._create_match_record(
                item, best_mapping, best_method, best_score
            )
        
        # 匹配失败
        record = MatchRecord(
            order_id=item.order_id,
            order_item_id=item.id,
            match_method=best_method,
            confidence_score=best_score,
            is_matched=False,
            failure_reason="No suitable match found"
        )
        self.db.add(record)
        return record

    async def _match_by_sku_code(self, sku_code: str) -> Optional[SKUMapping]:
        """通过SKU编码精确匹配"""
        stmt = select(SKUMapping).where(
            SKUMapping.tiktok_sku_id == sku_code,
            SKUMapping.status == "active"
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _match_by_name_similarity(
        self, item: OrderItem
    ) -> tuple[Optional[SKUMapping], float]:
        """通过名称相似度匹配"""
        # 获取所有活跃的SKU映射
        stmt = select(SKUMapping).where(SKUMapping.status == "active")
        result = await self.db.execute(stmt)
        mappings = result.scalars().all()
        
        best_mapping = None
        best_score = 0.0
        
        for mapping in mappings:
            if mapping.tiktok_sku_name and item.product_name:
                score = self._calculate_name_similarity(
                    mapping.tiktok_sku_name, item.product_name
                )
                if score > best_score:
                    best_score = score
                    best_mapping = mapping
        
        return best_mapping, best_score

    async def _match_by_image_similarity(
        self, item: OrderItem
    ) -> tuple[Optional[SKUMapping], float]:
        """通过图片相似度匹配"""
        # 获取商品图片URL
        product = await self._get_product(item.product_id)
        if not product or not product.images:
            return None, 0.0
        
        tiktok_image_url = product.images[0] if product.images else None
        if not tiktok_image_url:
            return None, 0.0
        
        # 获取所有活跃的SKU映射
        stmt = select(SKUMapping).where(SKUMapping.status == "active")
        result = await self.db.execute(stmt)
        mappings = result.scalars().all()
        
        best_mapping = None
        best_score = 0.0
        
        for mapping in mappings:
            if mapping.alibaba_image_url:
                score = await self._calculate_image_similarity(
                    tiktok_image_url, mapping.alibaba_image_url
                )
                if score > best_score:
                    best_score = score
                    best_mapping = mapping
        
        return best_mapping, best_score

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        计算名称相似度
        
        使用简单的关键词匹配和编辑距离
        生产环境建议使用更专业的NLP模型
        """
        # TODO: 集成专业的NLP模型进行相似度计算
        # 当前使用简单的关键词匹配
        keywords1 = set(name1.lower().split())
        keywords2 = set(name2.lower().split())
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        return len(intersection) / len(union)

    async def _calculate_image_similarity(
        self, image_url1: str, image_url2: str
    ) -> float:
        """
        计算图片相似度
        
        使用图像哈希或深度学习模型
        生产环境建议使用CLIP等模型
        """
        # TODO: 集成专业的图像相似度模型
        # Mock实现: 返回固定值
        return 0.85

    def _create_match_record(
        self,
        item: OrderItem,
        mapping: SKUMapping,
        method: MatchMethod,
        confidence: float
    ) -> MatchRecord:
        """创建匹配记录"""
        record = MatchRecord(
            order_id=item.order_id,
            order_item_id=item.id,
            sku_mapping_id=mapping.id,
            match_method=method,
            confidence_score=confidence,
            is_matched=True,
            match_details={
                "tiktok_sku_id": mapping.tiktok_sku_id,
                "alibaba_sku_id": mapping.alibaba_sku_id,
                "alibaba_product_id": mapping.alibaba_product_id
            }
        )
        self.db.add(record)
        return record

    async def _get_order_with_items(self, order_id: str) -> Optional[Order]:
        """获取订单及其商品项"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_product(self, product_id: str) -> Optional[Product]:
        """获取商品信息"""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_sku_mapping(
        self,
        tiktok_product_id: str,
        tiktok_sku_id: str,
        alibaba_product_id: str,
        alibaba_sku_id: str,
        match_method: MatchMethod,
        **kwargs
    ) -> SKUMapping:
        """创建新的SKU映射"""
        mapping = SKUMapping(
            tiktok_product_id=tiktok_product_id,
            tiktok_sku_id=tiktok_sku_id,
            alibaba_product_id=alibaba_product_id,
            alibaba_sku_id=alibaba_sku_id,
            match_method=match_method,
            **kwargs
        )
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def update_mapping_confidence(
        self, mapping_id: str, confidence_score: float
    ) -> Optional[SKUMapping]:
        """更新映射的置信度分数"""
        stmt = select(SKUMapping).where(SKUMapping.id == mapping_id)
        result = await self.db.execute(stmt)
        mapping = result.scalar_one_or_none()
        
        if mapping:
            mapping.confidence_score = confidence_score
            await self.db.commit()
            await self.db.refresh(mapping)
        
        return mapping
