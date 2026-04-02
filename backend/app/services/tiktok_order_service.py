"""TikTok订单同步服务"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.tiktok_service import TikTokShopService
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.product import Product

logger = logging.getLogger(__name__)


class TikTokOrderSyncService:
    """TikTok订单同步服务"""
    
    # TikTok订单状态映射
    ORDER_STATUS_MAP = {
        "AWAITING_COLLECTION": "pending",
        "AWAITING_SHIPMENT": "confirmed",
        "IN_TRANSIT": "shipped",
        "DELIVERED": "completed",
        "CANCELLED": "cancelled",
    }
    
    def __init__(self, db: AsyncSession):
        """初始化订单同步服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.tiktok_service = TikTokShopService()
    
    async def sync_orders(
        self,
        update_time_from: Optional[datetime] = None,
        update_time_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """同步TikTok订单
        
        Args:
            update_time_from: 更新时间起始
            update_time_to: 更新时间结束
        
        Returns:
            同步结果统计
        """
        # 如果未指定时间范围,默认同步最近24小时的订单
        if not update_time_from:
            update_time_from = datetime.utcnow() - timedelta(hours=24)
        if not update_time_to:
            update_time_to = datetime.utcnow()
        
        # 转换为Unix时间戳
        timestamp_from = int(update_time_from.timestamp())
        timestamp_to = int(update_time_to.timestamp())
        
        # 分页获取订单
        page = 1
        page_size = 50
        has_more = True
        total_synced = 0
        total_created = 0
        total_updated = 0
        errors = []
        
        while has_more:
            try:
                # 调用TikTok API
                result = await self.tiktok_service.get_orders(
                    page=page,
                    page_size=page_size,
                    update_time_from=timestamp_from,
                    update_time_to=timestamp_to
                )
                
                if result.get("code") != 0:
                    logger.error(f"TikTok API error: {result.get('message')}")
                    errors.append(result.get("message"))
                    break
                
                data = result.get("data", {})
                orders = data.get("orders", [])
                has_more = data.get("has_more", False)
                
                # 处理每个订单
                for order_data in orders:
                    try:
                        created, updated = await self._process_order(order_data)
                        total_synced += 1
                        if created:
                            total_created += 1
                        if updated:
                            total_updated += 1
                    except Exception as e:
                        logger.error(f"Error processing order {order_data.get('order_id')}: {e}")
                        errors.append(f"Order {order_data.get('order_id')}: {str(e)}")
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error syncing orders (page {page}): {e}")
                errors.append(f"Page {page}: {str(e)}")
                break
        
        return {
            "total_synced": total_synced,
            "total_created": total_created,
            "total_updated": total_updated,
            "errors": errors[:10] if errors else [],  # 只返回前10个错误
            "sync_time": datetime.utcnow().isoformat()
        }
    
    async def _process_order(self, order_data: Dict[str, Any]) -> tuple[bool, bool]:
        """处理单个订单
        
        Args:
            order_data: TikTok订单数据
        
        Returns:
            (是否新建, 是否更新)
        """
        tiktok_order_id = order_data.get("order_id")
        
        # 检查订单是否已存在
        stmt = select(Order).where(Order.tiktok_order_id == tiktok_order_id)
        result = await self.db.execute(stmt)
        existing_order = result.scalar_one_or_none()
        
        # 映射订单状态
        tiktok_status = order_data.get("order_status")
        mapped_status = self.ORDER_STATUS_MAP.get(tiktok_status, "pending")
        
        if existing_order:
            # 更新现有订单
            updated = await self._update_order(existing_order, order_data, mapped_status)
            return False, updated
        else:
            # 创建新订单
            await self._create_order(order_data, mapped_status)
            return True, False
    
    async def _create_order(self, order_data: Dict[str, Any], status: str) -> Order:
        """创建新订单"""
        # 解析订单数据
        order = Order(
            tiktok_order_id=order_data.get("order_id"),
            status=status,
            total_amount=order_data.get("total_amount", 0),
            currency=order_data.get("currency", "USD"),
            buyer_name=order_data.get("buyer", {}).get("name"),
            buyer_phone=order_data.get("buyer", {}).get("phone"),
            shipping_address=order_data.get("shipping_address"),
            tracking_number=order_data.get("tracking_number"),
            remark=order_data.get("remark")
        )
        
        self.db.add(order)
        await self.db.flush()  # 获取order.id
        
        # 创建订单项
        items = order_data.get("items", [])
        for item_data in items:
            # 尝试匹配本地商品
            product_id = await self._match_product(item_data.get("sku_id"))
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                product_name=item_data.get("product_name"),
                sku_code=item_data.get("sku_id"),
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("price"),
                subtotal=item_data.get("price") * item_data.get("quantity", 1)
            )
            self.db.add(order_item)
        
        # 创建状态历史
        status_history = OrderStatusHistory(
            order_id=order.id,
            from_status=None,
            to_status=status,
            remark="Order created from TikTok Shop"
        )
        self.db.add(status_history)
        
        await self.db.commit()
        
        logger.info(f"Created new order: {order.tiktok_order_id}")
        return order
    
    async def _update_order(
        self,
        order: Order,
        order_data: Dict[str, Any],
        new_status: str
    ) -> bool:
        """更新现有订单
        
        Returns:
            是否有更新
        """
        updated = False
        old_status = order.status
        
        # 检查状态是否变化
        if new_status != old_status:
            order.status = new_status
            
            # 创建状态变更历史
            status_history = OrderStatusHistory(
                order_id=order.id,
                from_status=old_status,
                to_status=new_status,
                remark=f"Status updated from TikTok: {order_data.get('order_status')}"
            )
            self.db.add(status_history)
            updated = True
        
        # 更新物流信息
        tracking_number = order_data.get("tracking_number")
        if tracking_number and tracking_number != order.tracking_number:
            order.tracking_number = tracking_number
            updated = True
        
        if updated:
            await self.db.commit()
            logger.info(f"Updated order: {order.tiktok_order_id}")
        
        return updated
    
    async def _match_product(self, sku_code: str) -> Optional[str]:
        """根据SKU编码匹配本地商品
        
        Args:
            sku_code: TikTok的SKU编码
        
        Returns:
            本地商品ID或None
        """
        if not sku_code:
            return None
        
        # 尝试从ProductSKU表查找
        from app.models.product import ProductSKU
        
        stmt = select(ProductSKU).where(ProductSKU.sku_code == sku_code)
        result = await self.db.execute(stmt)
        sku = result.scalar_one_or_none()
        
        if sku:
            return str(sku.product_id)
        
        return None
    
    async def get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情(从TikTok API)"""
        return await self.tiktok_service.get_order_detail(order_id)
    
    async def update_tracking_number(
        self,
        order_id: str,
        tracking_number: str
    ) -> Dict[str, Any]:
        """更新物流单号到TikTok"""
        return await self.tiktok_service.update_order_status(
            order_id=order_id,
            status="SHIPPED",
            tracking_number=tracking_number
        )
