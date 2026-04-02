"""Base adapter class for forwarder/logistics providers."""

from abc import ABC, abstractmethod
from typing import Optional


class ForwarderAdapter(ABC):
    """
    货代适配器抽象基类
    
    定义统一的货代接口,支持多种货代系统的对接
    """

    def __init__(self, config: dict):
        """
        初始化适配器
        
        Args:
            config: 货代配置信息
        """
        self.config = config
        self.forwarder_code = config.get("code")
        self.api_endpoint = config.get("api_endpoint")
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")

    @abstractmethod
    async def create_shipment(
        self,
        order_info: dict,
        items: list[dict],
        address: dict
    ) -> Optional[dict]:
        """
        创建运单
        
        Args:
            order_info: 订单信息
            items: 商品列表
            address: 收货地址
            
        Returns:
            {
                "tracking_number": str,
                "shipping_method": str,
                "estimated_delivery": str,
                "cost": float,
                "label_url": str
            }
        """
        pass

    @abstractmethod
    async def get_tracking_info(self, tracking_number: str) -> Optional[dict]:
        """
        获取物流轨迹信息
        
        Args:
            tracking_number: 运单号
            
        Returns:
            {
                "status": str,
                "location": str,
                "events": [
                    {
                        "time": str,
                        "location": str,
                        "description": str
                    }
                ]
            }
        """
        pass

    @abstractmethod
    async def get_shipping_methods(
        self,
        from_country: str,
        to_country: str,
        weight_kg: float
    ) -> list[dict]:
        """
        获取可用运输方式
        
        Args:
            from_country: 发货国家
            to_country: 目的国家
            weight_kg: 重量(kg)
            
        Returns:
            [
                {
                    "code": str,
                    "name": str,
                    "estimated_days": int,
                    "cost": float
                }
            ]
        """
        pass

    @abstractmethod
    async def calculate_shipping_cost(
        self,
        to_country: str,
        weight_kg: float,
        shipping_method: str
    ) -> Optional[float]:
        """
        计算运费
        
        Args:
            to_country: 目的国家
            weight_kg: 重量(kg)
            shipping_method: 运输方式
            
        Returns:
            运费金额
        """
        pass

    @abstractmethod
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """
        取消运单
        
        Args:
            tracking_number: 运单号
            
        Returns:
            是否取消成功
        """
        pass

    async def validate_address(self, address: dict) -> tuple[bool, Optional[str]]:
        """
        验证地址有效性
        
        Args:
            address: 地址信息
            
        Returns:
            (是否有效, 错误信息)
        """
        required_fields = ["country", "state", "city", "address", "recipient_name", "phone"]

        for field in required_fields:
            if not address.get(field):
                return False, f"Missing required field: {field}"

        return True, None

    async def format_address_for_api(self, address: dict) -> dict:
        """
        格式化地址供API使用
        
        Args:
            address: 原始地址
            
        Returns:
            格式化后的地址
        """
        # 子类可以重写此方法以适配不同的API格式
        return address
