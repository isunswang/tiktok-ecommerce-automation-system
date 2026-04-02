"""Intent classification service using GPT-4o."""

import logging
from enum import StrEnum
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class IntentType(StrEnum):
    """Customer service intent types."""
    # 商品相关
    PRODUCT_INQUIRY = "product_inquiry"  # 商品咨询
    STOCK_CHECK = "stock_check"  # 库存查询
    PRICE_INQUIRY = "price_inquiry"  # 价格咨询
    
    # 物流相关
    SHIPPING_INQUIRY = "shipping_inquiry"  # 物流咨询
    TRACKING_REQUEST = "tracking_request"  # 物流查询
    DELIVERY_TIME = "delivery_time"  # 送达时间
    
    # 订单相关
    ORDER_STATUS = "order_status"  # 订单状态
    ORDER_CANCEL = "order_cancel"  # 取消订单
    ORDER_MODIFY = "order_modify"  # 修改订单
    
    # 售后相关
    RETURN_REQUEST = "return_request"  # 退货
    REFUND_REQUEST = "refund_request"  # 退款
    COMPLAINT = "complaint"  # 投诉
    
    # 其他
    COUPON_INQUIRY = "coupon_inquiry"  # 优惠券咨询
    GENERAL_INQUIRY = "general_inquiry"  # 通用咨询
    UNKNOWN = "unknown"  # 无法识别


class IntentClassifier:
    """Intent classification service using GPT-4o."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = getattr(settings, 'INTENT_CLASSIFICATION_MODEL', 'gpt-4o-mini')
        self.mock_mode = getattr(settings, 'OPENAI_MOCK_MODE', True)

    async def classify_intent(
        self,
        message: str,
        context: Optional[dict] = None,
        language: str = "en"
    ) -> dict:
        """
        分类用户意图
        
        Args:
            message: 用户消息
            context: 上下文信息(订单历史、商品信息等)
            language: 语言代码
            
        Returns:
            {
                "intent": str,
                "confidence": float,
                "entities": dict,
                "suggested_action": str
            }
        """
        if self.mock_mode:
            return self._mock_classify(message)

        try:
            # 构造提示词
            system_prompt = self._build_system_prompt(language)
            user_prompt = self._build_user_prompt(message, context)

            # 调用GPT-4o
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            # 解析响应
            result = self._parse_gpt_response(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"Failed to classify intent: {e}", exc_info=True)
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "entities": {},
                "suggested_action": "transfer_to_human"
            }

    def _build_system_prompt(self, language: str) -> str:
        """构建系统提示词"""
        if language == "zh":
            return """
你是一个专业的客服意图分类助手。分析用户消息,识别其意图类型。

意图类型包括:
- product_inquiry: 商品咨询
- stock_check: 库存查询
- price_inquiry: 价格咨询
- shipping_inquiry: 物流咨询
- tracking_request: 物流查询
- delivery_time: 送达时间
- order_status: 订单状态
- order_cancel: 取消订单
- order_modify: 修改订单
- return_request: 退货
- refund_request: 退款
- complaint: 投诉
- coupon_inquiry: 优惠券咨询
- general_inquiry: 通用咨询
- unknown: 无法识别

请以JSON格式返回:
{
  "intent": "意图类型",
  "confidence": 0.95,
  "entities": {
    "order_id": "订单号",
    "product_name": "商品名称"
  },
  "suggested_action": "建议的下一步操作"
}
"""
        else:
            return """
You are a professional customer service intent classifier. Analyze user messages and identify their intent.

Intent types include:
- product_inquiry: Product information
- stock_check: Stock availability
- price_inquiry: Price inquiry
- shipping_inquiry: Shipping information
- tracking_request: Tracking request
- delivery_time: Delivery time
- order_status: Order status
- order_cancel: Cancel order
- order_modify: Modify order
- return_request: Return request
- refund_request: Refund request
- complaint: Complaint
- coupon_inquiry: Coupon inquiry
- general_inquiry: General inquiry
- unknown: Unknown intent

Please return in JSON format:
{
  "intent": "intent_type",
  "confidence": 0.95,
  "entities": {
    "order_id": "order_id",
    "product_name": "product_name"
  },
  "suggested_action": "suggested_next_action"
}
"""

    def _build_user_prompt(self, message: str, context: Optional[dict]) -> str:
        """构建用户提示词"""
        prompt = f"User message: {message}\n\n"
        
        if context:
            prompt += f"Context:\n"
            if context.get("order_history"):
                prompt += f"- Order history: {context['order_history']}\n"
            if context.get("current_product"):
                prompt += f"- Current product: {context['current_product']}\n"
        
        prompt += "\nPlease classify the intent and extract entities."
        return prompt

    def _parse_gpt_response(self, response: str) -> dict:
        """解析GPT响应"""
        import json
        
        try:
            # 尝试提取JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            # 如果无法提取JSON,返回默认值
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "entities": {},
                "suggested_action": "transfer_to_human"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse GPT response: {e}")
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "entities": {},
                "suggested_action": "transfer_to_human"
            }

    def _mock_classify(self, message: str) -> dict:
        """Mock意图分类"""
        message_lower = message.lower()
        
        # 简单的关键词匹配
        if any(word in message_lower for word in ["发货", "配送", "ship", "delivery"]):
            return {
                "intent": IntentType.SHIPPING_INQUIRY,
                "confidence": 0.85,
                "entities": {},
                "suggested_action": "check_shipping_policy"
            }
        elif any(word in message_lower for word in ["订单", "order"]):
            return {
                "intent": IntentType.ORDER_STATUS,
                "confidence": 0.90,
                "entities": {},
                "suggested_action": "check_order_status"
            }
        elif any(word in message_lower for word in ["退货", "退款", "return", "refund"]):
            return {
                "intent": IntentType.RETURN_REQUEST,
                "confidence": 0.88,
                "entities": {},
                "suggested_action": "initiate_return"
            }
        else:
            return {
                "intent": IntentType.GENERAL_INQUIRY,
                "confidence": 0.70,
                "entities": {},
                "suggested_action": "provide_general_info"
            }
