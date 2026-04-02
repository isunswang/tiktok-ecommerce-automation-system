"""Logistics service for managing shipments and tracking."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import Shipment, ShipmentStatus
from app.models.order import Order, OrderStatus
from app.models.fulfillment import Forwarder
from app.services.forwarders.yuntu_adapter import YuntuAdapter
from app.services.forwarders.yanwen_adapter import YanwenAdapter
from app.services.forwarders.d4px_adapter import D4PXAdapter
from app.services.tiktok_service import TikTokShopService

logger = logging.getLogger(__name__)


class LogisticsService:
    """Service for logistics and shipment management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tiktok_service = TikTokShopService()
        
        # 货代适配器映射
        self.forwarder_adapters = {
            "yuntu": YuntuAdapter,
            "yanwen": YanwenAdapter,
            "d4px": D4PXAdapter
        }

    async def create_shipment_for_order(
        self,
        order_id: str,
        forwarder_code: str
    ) -> Optional[Shipment]:
        """
        为订单创建运单
        
        Args:
            order_id: 订单ID
            forwarder_code: 货代代码
            
        Returns:
            创建的运单,失败返回None
        """
        # 获取订单
        order = await self._get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return None

        # 获取货代配置
        forwarder = await self._get_forwarder(forwarder_code)
        if not forwarder:
            logger.error(f"Forwarder {forwarder_code} not found")
            return None

        # 初始化货代适配器
        adapter_class = self.forwarder_adapters.get(forwarder_code)
        if not adapter_class:
            logger.error(f"No adapter found for forwarder {forwarder_code}")
            return None

        adapter = adapter_class({
            "code": forwarder.code,
            "api_endpoint": forwarder.api_endpoint,
            "api_key": forwarder.api_key,
            "api_secret": forwarder.api_secret
        })

        # 构造订单信息
        order_info = {
            "order_id": str(order.id),
            "tiktok_order_id": order.tiktok_order_id
        }

        # 构造商品列表
        items = []
        for item in order.items:
            items.append({
                "sku": item.sku_code,
                "name": item.product_name,
                "quantity": item.quantity,
                "value": float(item.unit_price)
            })

        # 构造收货地址
        address = order.shipping_address or {}

        # 调用货代API创建运单
        shipment_result = await adapter.create_shipment(order_info, items, address)
        
        if not shipment_result:
            logger.error(f"Failed to create shipment for order {order_id}")
            return None

        # 创建运单记录
        shipment = Shipment(
            order_id=order.id,
            tracking_number=shipment_result["tracking_number"],
            carrier=forwarder.name,
            status=ShipmentStatus.PENDING,
            estimated_delivery=shipment_result.get("estimated_delivery"),
            origin="China",
            destination=address.get("country", "Unknown")
        )
        
        self.db.add(shipment)
        await self.db.commit()
        await self.db.refresh(shipment)
        
        logger.info(f"Created shipment {shipment.id} for order {order_id}")
        return shipment

    async def update_tracking_info(self, tracking_number: str) -> Optional[dict]:
        """
        更新物流轨迹信息
        
        Args:
            tracking_number: 运单号
            
        Returns:
            物流轨迹信息
        """
        # 获取运单
        shipment = await self._get_shipment_by_tracking(tracking_number)
        if not shipment:
            logger.error(f"Shipment with tracking {tracking_number} not found")
            return None

        # 获取货代
        forwarder_code = self._get_forwarder_code_from_carrier(shipment.carrier)
        if not forwarder_code:
            logger.error(f"Unknown carrier: {shipment.carrier}")
            return None

        forwarder = await self._get_forwarder(forwarder_code)
        if not forwarder:
            return None

        # 初始化适配器
        adapter_class = self.forwarder_adapters.get(forwarder_code)
        adapter = adapter_class({
            "code": forwarder.code,
            "api_endpoint": forwarder.api_endpoint,
            "api_key": forwarder.api_key,
            "api_secret": forwarder.api_secret
        })

        # 获取轨迹信息
        tracking_info = await adapter.get_tracking_info(tracking_number)
        
        if tracking_info:
            # 更新运单状态
            shipment.logistics_events = tracking_info.get("events", [])
            
            # 更新状态
            status_mapping = {
                "in_transit": ShipmentStatus.IN_TRANSIT,
                "delivered": ShipmentStatus.DELIVERED,
                "exception": ShipmentStatus.EXCEPTION
            }
            
            new_status = status_mapping.get(tracking_info.get("status"))
            if new_status:
                shipment.status = new_status
            
            await self.db.commit()
            await self.db.refresh(shipment)
        
        return tracking_info

    async def upload_tracking_to_tiktok(
        self,
        order_id: str,
        tracking_number: str
    ) -> bool:
        """
        回传物流单号到TikTok
        
        Args:
            order_id: 订单ID
            tracking_number: 运单号
            
        Returns:
            是否成功
        """
        # 获取订单
        order = await self._get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return False

        try:
            # 调用TikTok API更新物流单号
            result = await self.tiktok_service.update_order_status(
                order.tiktok_order_id,
                tracking_number=tracking_number
            )
            
            if result:
                # 更新订单状态
                order.tracking_number = tracking_number
                await self.db.commit()
                
                logger.info(f"Tracking number {tracking_number} uploaded to TikTok for order {order_id}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to upload tracking to TikTok: {e}", exc_info=True)
            return False

    async def sync_logistics_status(self, limit: int = 50) -> int:
        """
        同步物流状态
        
        Args:
            limit: 同步数量限制
            
        Returns:
            成功同步的数量
        """
        # 获取在途运单
        stmt = select(Shipment).where(
            Shipment.status == ShipmentStatus.IN_TRANSIT
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        shipments = result.scalars().all()

        success_count = 0
        for shipment in shipments:
            try:
                tracking_info = await self.update_tracking_info(shipment.tracking_number)
                if tracking_info:
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to sync shipment {shipment.id}: {e}")

        logger.info(f"Synced {success_count}/{len(shipments)} shipments")
        return success_count

    async def _get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_forwarder(self, forwarder_code: str) -> Optional[Forwarder]:
        """获取货代"""
        stmt = select(Forwarder).where(Forwarder.code == forwarder_code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_shipment_by_tracking(self, tracking_number: str) -> Optional[Shipment]:
        """根据运单号获取运单"""
        stmt = select(Shipment).where(Shipment.tracking_number == tracking_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _get_forwarder_code_from_carrier(self, carrier_name: str) -> Optional[str]:
        """从承运商名称获取货代代码"""
        mapping = {
            "云途物流": "yuntu",
            "燕文物流": "yanwen",
            "递四方": "d4px"
        }
        return mapping.get(carrier_name)
