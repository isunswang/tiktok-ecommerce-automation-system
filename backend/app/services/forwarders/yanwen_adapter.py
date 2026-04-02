"""Yanwen (燕文) forwarder adapter."""

import logging
from typing import Optional

import httpx

from app.services.forwarders.base_adapter import ForwarderAdapter

logger = logging.getLogger(__name__)


class YanwenAdapter(ForwarderAdapter):
    """燕文物流适配器"""

    async def create_shipment(
        self,
        order_info: dict,
        items: list[dict],
        address: dict
    ) -> Optional[dict]:
        """创建燕文运单"""
        try:
            # Mock模式
            if not self.api_key:
                return self._mock_create_shipment(order_info, items)

            # 格式化地址
            formatted_address = await self.format_address_for_api(address)

            # 构造请求
            payload = {
                "orderNo": order_info.get("order_id"),
                "receiverInfo": {
                    "name": formatted_address.get("recipient_name"),
                    "mobile": formatted_address.get("phone"),
                    "countryCode": formatted_address.get("country"),
                    "province": formatted_address.get("state"),
                    "city": formatted_address.get("city"),
                    "address": formatted_address.get("address"),
                    "postcode": formatted_address.get("postal_code")
                },
                "productList": [
                    {
                        "productSku": item.get("sku"),
                        "productName": item.get("name"),
                        "productQuantity": item.get("quantity"),
                        "productPrice": item.get("value")
                    }
                    for item in items
                ],
                "channelCode": "YW_STANDARD"
            }

            # 调用燕文API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/api/orders",
                    json=payload,
                    headers={
                        "Authorization": self.api_key,
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "tracking_number": result.get("trackingNo"),
                    "shipping_method": "YW_STANDARD",
                    "estimated_delivery": result.get("estimatedDeliveryTime"),
                    "cost": result.get("totalFee"),
                    "label_url": result.get("labelUrl")
                }

        except Exception as e:
            logger.error(f"Failed to create Yanwen shipment: {e}", exc_info=True)
            return None

    async def get_tracking_info(self, tracking_number: str) -> Optional[dict]:
        """获取燕文物流轨迹"""
        try:
            if not self.api_key:
                return self._mock_tracking_info(tracking_number)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_endpoint}/api/track/{tracking_number}",
                    headers={
                        "Authorization": self.api_key
                    }
                )
                response.raise_for_status()
                
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get Yanwen tracking: {e}", exc_info=True)
            return None

    async def get_shipping_methods(
        self,
        from_country: str,
        to_country: str,
        weight_kg: float
    ) -> list[dict]:
        """获取燕文运输方式"""
        # Mock数据
        return [
            {
                "code": "YW_STANDARD",
                "name": "燕文航空专线",
                "estimated_days": 12,
                "cost": 45.0 + weight_kg * 18.0
            },
            {
                "code": "YW_ECONOMY",
                "name": "燕文经济快递",
                "estimated_days": 18,
                "cost": 35.0 + weight_kg * 12.0
            }
        ]

    async def calculate_shipping_cost(
        self,
        to_country: str,
        weight_kg: float,
        shipping_method: str
    ) -> Optional[float]:
        """计算燕文运费"""
        methods = await self.get_shipping_methods("CN", to_country, weight_kg)
        
        for method in methods:
            if method["code"] == shipping_method:
                return method["cost"]
        
        return None

    async def cancel_shipment(self, tracking_number: str) -> bool:
        """取消燕文运单"""
        try:
            if not self.api_key:
                logger.info(f"[MOCK] Cancelled Yanwen shipment {tracking_number}")
                return True

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/api/orders/{tracking_number}/cancel",
                    headers={
                        "Authorization": self.api_key
                    }
                )
                response.raise_for_status()
                
                return True

        except Exception as e:
            logger.error(f"Failed to cancel Yanwen shipment: {e}", exc_info=True)
            return False

    async def format_address_for_api(self, address: dict) -> dict:
        """格式化地址供燕文API使用"""
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
            "tracking_number": f"YW{order_info.get('order_id', '123456')}",
            "shipping_method": "YW_STANDARD",
            "estimated_delivery": "2025-01-18",
            "cost": 72.0,
            "label_url": "https://example.com/label.pdf"
        }

    def _mock_tracking_info(self, tracking_number: str) -> dict:
        """Mock物流轨迹"""
        return {
            "status": "in_transit",
            "location": "Shenzhen, China",
            "events": [
                {
                    "time": "2025-01-01 09:00:00",
                    "location": "Shenzhen",
                    "description": "Order received"
                },
                {
                    "time": "2025-01-01 18:00:00",
                    "location": "Shenzhen Sorting Center",
                    "description": "Departed facility"
                }
            ]
        }
