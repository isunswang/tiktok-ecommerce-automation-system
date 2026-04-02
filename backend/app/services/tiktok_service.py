"""TikTok Shop API服务封装"""

import hashlib
import hmac
import time
import logging
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime

from app.config import get_settings

logger = logging.getLogger(__name__)


class TikTokShopService:
    """TikTok Shop API服务
    
    官方文档: https://partner.tiktokshop.com/docv2/page/
    """
    
    def __init__(self):
        """初始化TikTok Shop服务"""
        self.settings = get_settings()
        self.api_url = self.settings.tiktok_shop_api_url
        self.app_key = self.settings.tiktok_shop_app_key
        self.app_secret = self.settings.tiktok_shop_app_secret
        self.access_token = self.settings.tiktok_shop_access_token
        self.mock_mode = self.settings.tiktok_shop_mock_mode
        
        if not self.mock_mode and not self.app_key:
            raise ValueError("TikTok Shop app_key is required when mock mode is disabled")
    
    async def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """发送API请求"""
        if self.mock_mode:
            return self._mock_response(path, params, data)
        
        # 构造请求参数
        timestamp = int(time.time())
        params = params or {}
        params.update({
            "app_key": self.app_key,
            "timestamp": timestamp,
            "access_token": self.access_token
        })
        
        # 生成签名
        sign = self._generate_signature(method, path, params)
        params["sign"] = sign
        
        # 发送请求
        url = f"{self.api_url}{path}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, json=data, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
    
    def _generate_signature(self, method: str, path: str, params: Dict[str, Any]) -> str:
        """生成API签名
        
        TikTok Shop签名算法:
        1. 将所有参数按key字母顺序排序
        2. 拼接成 key1value1key2value2... 格式
        3. 在前后添加app_secret
        4. 进行HMAC-SHA256签名
        """
        # 排序参数
        sorted_params = sorted(params.items())
        
        # 拼接字符串
        sign_string = self.app_secret
        for key, value in sorted_params:
            if value is not None:
                sign_string += f"{key}{value}"
        sign_string += self.app_secret
        
        # HMAC-SHA256签名
        signature = hmac.new(
            self.app_secret.encode(),
            sign_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _mock_response(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock响应"""
        logger.info(f"[MOCK] TikTok API call: {path}")
        
        # 根据不同的path返回不同的mock数据
        if "product/create" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "product_id": "MOCK_PRODUCT_" + str(int(time.time()))
                }
            }
        elif "order/list" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "orders": [],
                    "total": 0,
                    "has_more": False
                }
            }
        else:
            return {
                "code": 0,
                "message": "success",
                "data": {}
            }
    
    # ===== 商品相关API =====
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建商品
        
        文档: https://partner.tiktokshop.com/docv2/page/
        """
        return await self._make_request("POST", "/api/products/create", data=product_data)
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新商品"""
        data = {"product_id": product_id, **product_data}
        return await self._make_request("POST", "/api/products/update", data=data)
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """获取商品详情"""
        params = {"product_id": product_id}
        return await self._make_request("GET", "/api/products/detail", params=params)
    
    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        """删除商品"""
        data = {"product_id": product_id}
        return await self._make_request("POST", "/api/products/delete", data=data)
    
    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取商品列表"""
        params = {
            "page_number": page,
            "page_size": page_size
        }
        if status:
            params["product_status"] = status
        
        return await self._make_request("GET", "/api/products/search", params=params)
    
    async def upload_image(self, image_url: str) -> Dict[str, Any]:
        """上传图片到TikTok"""
        data = {"image_url": image_url}
        return await self._make_request("POST", "/api/media/upload", data=data)
    
    # ===== 订单相关API =====
    
    async def get_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        update_time_from: Optional[int] = None,
        update_time_to: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取订单列表
        
        Args:
            page: 页码
            page_size: 每页数量
            update_time_from: 更新时间起始(Unix时间戳)
            update_time_to: 更新时间结束(Unix时间戳)
        """
        params = {
            "page_number": page,
            "page_size": page_size
        }
        
        if update_time_from:
            params["update_time_from"] = update_time_from
        if update_time_to:
            params["update_time_to"] = update_time_to
        
        return await self._make_request("GET", "/api/orders/search", params=params)
    
    async def get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情"""
        params = {"order_id": order_id}
        return await self._make_request("GET", "/api/orders/detail", params=params)
    
    async def update_order_status(
        self,
        order_id: str,
        status: str,
        tracking_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新订单状态"""
        data = {
            "order_id": order_id,
            "order_status": status
        }
        
        if tracking_number:
            data["tracking_number"] = tracking_number
        
        return await self._make_request("POST", "/api/orders/status/update", data=data)
    
    # ===== 类目相关API =====
    
    async def get_categories(self) -> Dict[str, Any]:
        """获取商品类目列表"""
        return await self._make_request("GET", "/api/categories")
    
    async def get_category_attributes(self, category_id: str) -> Dict[str, Any]:
        """获取类目属性"""
        params = {"category_id": category_id}
        return await self._make_request("GET", "/api/categories/attributes", params=params)
