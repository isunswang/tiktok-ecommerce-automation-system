"""Address management service for forwarder and shipping."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import Forwarder

logger = logging.getLogger(__name__)


class AddressService:
    """Service for managing forwarder addresses and shipping addresses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_forwarder_address(
        self,
        forwarder_code: str,
        country_code: Optional[str] = None
    ) -> Optional[dict]:
        """
        获取货代地址
        
        Args:
            forwarder_code: 货代代码 (yuntu, yanwen, d4px)
            country_code: 目标国家代码 (可选,用于多仓库选择)
            
        Returns:
            货代地址信息
        """
        # 获取货代信息
        stmt = select(Forwarder).where(
            Forwarder.code == forwarder_code,
            Forwarder.status == "active"
        )
        result = await self.db.execute(stmt)
        forwarder = result.scalar_one_or_none()
        
        if not forwarder:
            logger.error(f"Forwarder {forwarder_code} not found")
            return None

        # 根据国家代码选择仓库地址
        # Mock: 返回默认地址
        address = {
            "forwarder_id": str(forwarder.id),
            "forwarder_name": forwarder.name,
            "forwarder_code": forwarder.code,
            "contact_name": forwarder.contact_name,
            "contact_phone": forwarder.contact_phone,
            "province": forwarder.province,
            "city": forwarder.city,
            "district": forwarder.district,
            "address": forwarder.address,
            "postal_code": forwarder.postal_code,
        }
        
        return address

    async def format_shipping_address_for_1688(
        self,
        tiktok_address: dict,
        forwarder_address: dict
    ) -> dict:
        """
        格式化收货地址供1688下单使用
        
        Args:
            tiktok_address: TikTok买家地址
            forwarder_address: 货代地址
            
        Returns:
            格式化后的地址信息
        """
        # 1688下单地址格式
        formatted_address = {
            "receiverName": forwarder_address.get("contact_name", ""),
            "receiverMobile": forwarder_address.get("contact_phone", ""),
            "receiverPhone": forwarder_address.get("contact_phone", ""),
            "province": forwarder_address.get("province", ""),
            "city": forwarder_address.get("city", ""),
            "area": forwarder_address.get("district", ""),
            "address": forwarder_address.get("address", ""),
            "postCode": forwarder_address.get("postal_code", ""),
            # 订单备注: 包含TikTok订单信息
            "orderRemark": f"TikTok Order: {tiktok_address.get('order_id', '')} | "
                          f"Buyer: {tiktok_address.get('buyer_name', '')} | "
                          f"Phone: {tiktok_address.get('buyer_phone', '')}"
        }
        
        return formatted_address

    async def validate_shipping_address(self, address: dict) -> tuple[bool, Optional[str]]:
        """
        验证收货地址有效性
        
        Args:
            address: 收货地址
            
        Returns:
            (是否有效, 错误信息)
        """
        required_fields = [
            "receiverName",
            "receiverMobile",
            "province",
            "city",
            "address"
        ]
        
        for field in required_fields:
            if not address.get(field):
                return False, f"Missing required field: {field}"
        
        # 验证手机号格式
        mobile = address.get("receiverMobile", "")
        if not self._validate_chinese_mobile(mobile):
            return False, f"Invalid mobile number: {mobile}"
        
        return True, None

    def _validate_chinese_mobile(self, mobile: str) -> bool:
        """验证中国手机号格式"""
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, mobile))

    async def get_all_active_forwarders(self) -> list[Forwarder]:
        """获取所有活跃的货代"""
        stmt = select(Forwarder).where(Forwarder.status == "active")
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def select_best_forwarder(
        self,
        country_code: str,
        weight_kg: float
    ) -> Optional[Forwarder]:
        """
        选择最优货代
        
        Args:
            country_code: 目标国家代码
            weight_kg: 包裹重量(kg)
            
        Returns:
            最优货代
        """
        forwarders = await self.get_all_active_forwarders()
        
        if not forwarders:
            logger.error("No active forwarders found")
            return None

        # TODO: 实现基于价格、时效、服务质量的货代选择算法
        # 当前返回第一个可用货代
        return forwarders[0]

    async def create_forwarder(
        self,
        code: str,
        name: str,
        contact_name: str,
        contact_phone: str,
        province: str,
        city: str,
        district: str,
        address: str,
        postal_code: Optional[str] = None,
        **kwargs
    ) -> Forwarder:
        """创建货代记录"""
        forwarder = Forwarder(
            code=code,
            name=name,
            contact_name=contact_name,
            contact_phone=contact_phone,
            province=province,
            city=city,
            district=district,
            address=address,
            postal_code=postal_code,
            **kwargs
        )
        
        self.db.add(forwarder)
        await self.db.commit()
        await self.db.refresh(forwarder)
        
        logger.info(f"Created forwarder: {forwarder.id}")
        return forwarder
