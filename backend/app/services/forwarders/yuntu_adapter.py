"""Yuntu (云途) forwarder adapter."""

import logging
from typing import Optional

import httpx

from app.services.forwarders.base_adapter import ForwarderAdapter

logger = logging.getLogger(__name__)


class YuntuAdapter(ForwarderAdapter):
    """云途物流适配器"""

    async def create_shipment(
        self,
        order_info: dict,
        items: list[dict],
        address: dict
    ) -> Optional[dict]:
        """创建云途运单"""
        try:
            # Mock模式
            if not self.api_key:
                return self._mock_create_shipment(order_info, items)

            # 格式化地址
            formatted_address = await self.format_address_for_api(address)

            # 构造请求
            payload = {
                "orderNo": order_info.get("order_id"),
                "recipient": {
                    "name": formatted_address.get("recipient_name"),
                    "phone": formatted_address.get("phone"),
                    "country": formatted_address.get("country"),
                    "state": formatted_address.get("state"),
                    "city": formatted_address.get("city"),
                    "address": formatted_address.get("address"),
                    "postalCode": formatted_address.get("postal_code")
                },
                "items": [
                    {
                        "sku": item.get("sku"),
                        "name": item.get("name"),
                        "quantity": item.get("quantity"),
                        "value": item.get("value")
                    }
                    for item in items
                ],
                "shippingMethod": "YT_EXPRESS"
            }

            # 调用云途API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/shipments",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "tracking_number": result.get("trackingNumber"),
                    "shipping_method": "YT_EXPRESS",
                    "estimated_delivery": result.get("estimatedDelivery"),
                    "cost": result.get("cost"),
                    "label_url": result.get("labelUrl")
                }

        except Exception as e:
            logger.error(f"Failed to create Yuntu shipment: {e}", exc_info=True)
            return None

    async def get_tracking_info(self, tracking_number: str) -> Optional[dict]:
        """获取云途物流轨迹"""
        try:
            if not self.api_key:
                return self._mock_tracking_info(tracking_number)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_endpoint}/tracking/{tracking_number}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                response.raise_for_status()
                
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get Yuntu tracking: {e}", exc_info=True)
            return None

    async def get_shipping_methods(
        self,
        from_country: str,
        to_country: str,
        weight_kg: float
    ) -> list[dict]:
        """获取云途运输方式"""
        # Mock数据
        return [
            {
                "code": "YT_EXPRESS",
                "name": "云途全球专线",
                "estimated_days": 7,
                "cost": 50.0 + weight_kg * 20.0
            },
            {
                "code": "YT_STANDARD",
                "name": "云途标准快递",
                "estimated_days": 10,
                "cost": 40.0 + weight_kg * 15.0
            }
        ]

    async def calculate_shipping_cost(
        self,
        to_country: str,
        weight_kg: float,
        shipping_method: str
    ) -> Optional[float]:
        """计算云途运费"""
        methods = await self.get_shipping_methods("CN", to_country, weight_kg)
        
        for method in methods:
            if method["code"] == shipping_method:
                return method["cost"]
        
        return None

    async def cancel_shipment(self, tracking_number: str) -> bool:
        """取消云途运单"""
        try:
            if not self.api_key:
                logger.info(f"[MOCK] Cancelled Yuntu shipment {tracking_number}")
                return True

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.api_endpoint}/shipments/{tracking_number}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                response.raise_for_status()
                
                return True

        except Exception as e:
            logger.error(f"Failed to cancel Yuntu shipment: {e}", exc_info=True)
            return False

    async def format_address_for_api(self, address: dict) -> dict:
        """格式化地址供云途API使用"""
        return {
            "recipient_name": address.get("recipient_name") or address.get("buyer_name"),
            "phone": address.get("phone") or address.get("buyer_phone"),
            "country": address.get("country", "US"),
            "state": address.get("state") or address.get("province"),
            "city": address.get("city"),
            "address": address.get("address") or address.get("address_line_1"),
            "postal_code": address.get("postal_code")
        }

    def _mock_create_shipment(self, order_info: dict, items: list[dict]) -> dict:
        """Mock创建运单"""
        return {
            "tracking_number": f"YT{order_info.get('order_id', '123456')}",
            "shipping_method": "YT_EXPRESS",
            "estimated_delivery": "2025-01-15",
            "cost": 85.0,
            "label_url": "https://example.com/label.pdf"
        }

    def _mock_tracking_info(self, tracking_number: str) -> dict:
        """Mock物流轨迹"""
        return {
            "status": "in_transit",
            "location": "Shanghai, China",
            "events": [
                {
                    "time": "2025-01-01 10:00:00",
                    "location": "Shanghai",
                    "description": "Shipment picked up"
                },
                {
                    "time": "2025-01-02 15:00:00",
                    "location": "Shanghai Sorting Center",
                    "description": "In transit to destination"
                }
            ]
        }
