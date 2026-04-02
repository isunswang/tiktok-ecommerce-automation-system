"""D4PX (递四方) forwarder adapter."""

import logging
from typing import Optional

import httpx

from app.services.forwarders.base_adapter import ForwarderAdapter

logger = logging.getLogger(__name__)


class D4PXAdapter(ForwarderAdapter):
    """递四方物流适配器"""

    async def create_shipment(
        self,
        order_info: dict,
        items: list[dict],
        address: dict
    ) -> Optional[dict]:
        """创建递四方运单"""
        try:
            # Mock模式
            if not self.api_key:
                return self._mock_create_shipment(order_info, items)

            # 格式化地址
            formatted_address = await self.format_address_for_api(address)

            # 构造请求
            payload = {
                "orderNo": order_info.get("order_id"),
                "consignee": {
                    "name": formatted_address.get("recipient_name"),
                    "tel": formatted_address.get("phone"),
                    "country": formatted_address.get("country"),
                    "province": formatted_address.get("state"),
                    "city": formatted_address.get("city"),
                    "address": formatted_address.get("address"),
                    "postcode": formatted_address.get("postal_code")
                },
                "cargoList": [
                    {
                        "sku": item.get("sku"),
                        "nameCn": item.get("name"),
                        "count": item.get("quantity"),
                        "unitPrice": item.get("value"),
                        "unitWeight": item.get("weight", 0.1)
                    }
                    for item in items
                ],
                "channel": "D4PX_GLOBAL"
            }

            # 调用递四方API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/openapi/order/create",
                    json=payload,
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "tracking_number": result.get("trackingNo"),
                    "shipping_method": "D4PX_GLOBAL",
                    "estimated_delivery": result.get("deliveryTime"),
                    "cost": result.get("freight"),
                    "label_url": result.get("labelUrl")
                }

        except Exception as e:
            logger.error(f"Failed to create D4PX shipment: {e}", exc_info=True)
            return None

    async def get_tracking_info(self, tracking_number: str) -> Optional[dict]:
        """获取递四方物流轨迹"""
        try:
            if not self.api_key:
                return self._mock_tracking_info(tracking_number)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_endpoint}/openapi/track/{tracking_number}",
                    headers={
                        "X-API-KEY": self.api_key
                    }
                )
                response.raise_for_status()
                
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get D4PX tracking: {e}", exc_info=True)
            return None

    async def get_shipping_methods(
        self,
        from_country: str,
        to_country: str,
        weight_kg: float
    ) -> list[dict]:
        """获取递四方运输方式"""
        # Mock数据
        return [
            {
                "code": "D4PX_GLOBAL",
                "name": "递四方全球速递",
                "estimated_days": 8,
                "cost": 55.0 + weight_kg * 22.0
            },
            {
                "code": "D4PX_ECONOMY",
                "name": "递四方经济快递",
                "estimated_days": 15,
                "cost": 38.0 + weight_kg * 14.0
            }
        ]

    async def calculate_shipping_cost(
        self,
        to_country: str,
        weight_kg: float,
        shipping_method: str
    ) -> Optional[float]:
        """计算递四方运费"""
        methods = await self.get_shipping_methods("CN", to_country, weight_kg)
        
        for method in methods:
            if method["code"] == shipping_method:
                return method["cost"]
        
        return None

    async def cancel_shipment(self, tracking_number: str) -> bool:
        """取消递四方运单"""
        try:
            if not self.api_key:
                logger.info(f"[MOCK] Cancelled D4PX shipment {tracking_number}")
                return True

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/openapi/order/cancel",
                    json={"trackingNo": tracking_number},
                    headers={
                        "X-API-KEY": self.api_key
                    }
                )
                response.raise_for_status()
                
                return True

        except Exception as e:
            logger.error(f"Failed to cancel D4PX shipment: {e}", exc_info=True)
            return False

    async def format_address_for_api(self, address: dict) -> dict:
        """格式化地址供递四方API使用"""
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
            "tracking_number": f"D4PX{order_info.get('order_id', '123456')}",
            "shipping_method": "D4PX_GLOBAL",
            "estimated_delivery": "2025-01-12",
            "cost": 88.0,
            "label_url": "https://example.com/label.pdf"
        }

    def _mock_tracking_info(self, tracking_number: str) -> dict:
        """Mock物流轨迹"""
        return {
            "status": "in_transit",
            "location": "Guangzhou, China",
            "events": [
                {
                    "time": "2025-01-01 08:00:00",
                    "location": "Guangzhou",
                    "description": "Package received"
                },
                {
                    "time": "2025-01-01 20:00:00",
                    "location": "Guangzhou Hub",
                    "description": "Departed from origin facility"
                }
            ]
        }
