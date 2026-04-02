"""Purchase order service for 1688 procurement."""

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import PurchaseOrder, PurchaseOrderStatus
from app.models.mapping import MatchRecord
from app.models.order import Order, OrderItem

logger = logging.getLogger(__name__)


class PurchaseService:
    """Service for managing purchase orders from 1688."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_purchase_order_from_order(
        self, order_id: str
    ) -> Optional[PurchaseOrder]:
        """
        根据TikTok订单创建1688采购单
        
        Args:
            order_id: TikTok订单ID
            
        Returns:
            创建的采购单,失败返回None
        """
        # 获取订单及其匹配记录
        order = await self._get_order_with_matches(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return None

        # 检查是否已有采购单
        existing_po = await self._get_purchase_order_by_tiktok_order(order_id)
        if existing_po:
            logger.info(f"Purchase order already exists for order {order_id}")
            return existing_po

        # 按供应商分组订单项
        supplier_groups = await self._group_items_by_supplier(order)
        if not supplier_groups:
            logger.error(f"No supplier found for order {order_id}")
            return None

        # 为每个供应商创建采购单
        purchase_orders = []
        for supplier_id, items in supplier_groups.items():
            try:
                po = await self._create_purchase_order_for_supplier(
                    order, supplier_id, items
                )
                purchase_orders.append(po)
            except Exception as e:
                logger.error(f"Failed to create PO for supplier {supplier_id}: {e}", exc_info=True)

        # 返回第一个采购单(简化处理,实际可能需要合并)
        return purchase_orders[0] if purchase_orders else None

    async def _create_purchase_order_for_supplier(
        self,
        order: Order,
        supplier_id: str,
        items: list[dict]
    ) -> PurchaseOrder:
        """
        为指定供应商创建采购单
        
        Args:
            order: TikTok订单
            supplier_id: 供应商ID
            items: 订单项列表(包含匹配信息)
            
        Returns:
            创建的采购单
        """
        # 计算总金额
        total_amount = sum(item.get('price', Decimal('0')) * item.get('quantity', 1) for item in items)
        
        # 创建采购单
        po = PurchaseOrder(
            supplier_id=supplier_id,
            status=PurchaseOrderStatus.PENDING,
            total_amount=total_amount,
            currency="CNY",
            linked_order_ids=[str(order.id)],
            remark=f"Auto-generated from TikTok order {order.tiktok_order_id}"
        )
        
        self.db.add(po)
        await self.db.commit()
        await self.db.refresh(po)
        
        logger.info(f"Created purchase order {po.id} for order {order.id}")
        return po

    async def update_purchase_order_status(
        self,
        po_id: str,
        status: PurchaseOrderStatus,
        tracking_number: Optional[str] = None
    ) -> Optional[PurchaseOrder]:
        """
        更新采购单状态
        
        Args:
            po_id: 采购单ID
            status: 新状态
            tracking_number: 物流单号(可选)
            
        Returns:
            更新后的采购单
        """
        stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        result = await self.db.execute(stmt)
        po = result.scalar_one_or_none()
        
        if not po:
            logger.error(f"Purchase order {po_id} not found")
            return None

        po.status = status
        if tracking_number:
            po.tracking_number = tracking_number
        
        await self.db.commit()
        await self.db.refresh(po)
        
        logger.info(f"Updated PO {po_id} status to {status}")
        return po

    async def get_pending_purchase_orders(self, limit: int = 50) -> list[PurchaseOrder]:
        """获取待处理的采购单"""
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.status == PurchaseOrderStatus.PENDING
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_order_with_matches(self, order_id: str) -> Optional[Order]:
        """获取订单及其匹配记录"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_purchase_order_by_tiktok_order(self, order_id: str) -> Optional[PurchaseOrder]:
        """根据TikTok订单ID查找采购单"""
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.linked_order_ids.contains([order_id])
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _group_items_by_supplier(self, order: Order) -> dict[str, list[dict]]:
        """
        按供应商分组订单项
        
        Returns:
            {supplier_id: [item_info, ...]}
        """
        supplier_groups = {}
        
        for item in order.items:
            # 获取匹配记录
            match_record = await self._get_match_record(item.id)
            if not match_record or not match_record.is_matched:
                logger.warning(f"Item {item.id} not matched, skipping")
                continue
            
            # 获取SKU映射
            if not match_record.sku_mapping_id:
                logger.warning(f"No SKU mapping for item {item.id}")
                continue
            
            from app.models.mapping import SKUMapping
            stmt = select(SKUMapping).where(SKUMapping.id == match_record.sku_mapping_id)
            result = await self.db.execute(stmt)
            mapping = result.scalar_one_or_none()
            
            if not mapping or not mapping.supplier_id:
                logger.warning(f"No supplier for item {item.id}")
                continue
            
            supplier_id = str(mapping.supplier_id)
            
            if supplier_id not in supplier_groups:
                supplier_groups[supplier_id] = []
            
            supplier_groups[supplier_id].append({
                'item_id': str(item.id),
                'product_name': item.product_name,
                'quantity': item.quantity,
                'price': mapping.alibaba_price or item.unit_price,
                'alibaba_product_id': mapping.alibaba_product_id,
                'alibaba_sku_id': mapping.alibaba_sku_id
            })
        
        return supplier_groups

    async def _get_match_record(self, order_item_id: str) -> Optional[MatchRecord]:
        """获取订单项的匹配记录"""
        stmt = select(MatchRecord).where(MatchRecord.order_item_id == order_item_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def cancel_purchase_order(self, po_id: str, reason: str) -> Optional[PurchaseOrder]:
        """
        取消采购单
        
        Args:
            po_id: 采购单ID
            reason: 取消原因
            
        Returns:
            更新后的采购单
        """
        stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        result = await self.db.execute(stmt)
        po = result.scalar_one_or_none()
        
        if not po:
            logger.error(f"Purchase order {po_id} not found")
            return None

        po.status = PurchaseOrderStatus.CANCELLED
        po.remark = f"{po.remark or ''}\nCancelled: {reason}"
        
        await self.db.commit()
        await self.db.refresh(po)
        
        logger.info(f"Cancelled PO {po_id}: {reason}")
        return po
