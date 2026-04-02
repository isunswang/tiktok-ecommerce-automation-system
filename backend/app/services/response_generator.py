"""Response generation service using GPT-4o."""

import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings
from app.models.faq import FAQ

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """AI response generation service."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = getattr(settings, 'RESPONSE_GENERATION_MODEL', 'gpt-4o')
        self.mock_mode = getattr(settings, 'OPENAI_MOCK_MODE', True)

    async def generate_response(
        self,
        user_message: str,
        intent: str,
        entities: dict,
        context: dict,
        language: str = "en"
    ) -> str:
        """
        生成客服回复
        
        Args:
            user_message: 用户消息
            intent: 意图类型
            entities: 提取的实体
            context: 对话上下文
            language: 语言代码
            
        Returns:
            生成的回复
        """
        if self.mock_mode:
            return self._mock_generate_response(intent, language)

        try:
            # 构造提示词
            system_prompt = self._build_system_prompt(language)
            user_prompt = self._build_user_prompt(
                user_message, intent, entities, context
            )

            # 调用GPT-4o
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to generate response: {e}", exc_info=True)
            return self._get_fallback_response(language)

    async def generate_faq_response(
        self,
        faq: FAQ,
        language: str = "en"
    ) -> str:
        """基于FAQ生成回复"""
        if language == "zh" or language == "cn":
            return faq.answer
        else:
            return faq.answer_en or faq.answer

    async def personalize_response(
        self,
        template: str,
        variables: dict,
        language: str = "en"
    ) -> str:
        """
        个性化回复模板
        
        Args:
            template: 回复模板
            variables: 变量字典
            language: 语言代码
            
        Returns:
            个性化后的回复
        """
        # 简单的变量替换
        response = template
        for key, value in variables.items():
            response = response.replace(f"{{{key}}}", str(value))
        
        return response

    async def translate_response(
        self,
        text: str,
        target_language: str
    ) -> str:
        """
        翻译回复
        
        Args:
            text: 原始文本
            target_language: 目标语言
            
        Returns:
            翻译后的文本
        """
        if self.mock_mode:
            return f"[Translated to {target_language}]: {text}"

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate the following text to {target_language}."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to translate: {e}", exc_info=True)
            return text

    def _build_system_prompt(self, language: str) -> str:
        """构建系统提示词"""
        if language == "zh":
            return """
你是一个专业、友好、耐心的跨境电商客服助手。你的职责是:

1. 准确理解用户的问题和需求
2. 提供清晰、有帮助的回答
3. 保持专业和礼貌的语气
4. 在无法回答时,诚实告知并建议转人工

回复要求:
- 使用简单易懂的语言
- 提供具体的信息和解决方案
- 如果涉及订单,请先确认订单号
- 如果需要转人工,请礼貌告知

请用中文回复。
"""
        else:
            return """
You are a professional, friendly, and patient cross-border e-commerce customer service assistant. Your responsibilities are:

1. Accurately understand user questions and needs
2. Provide clear, helpful answers
3. Maintain a professional and polite tone
4. When unable to answer, be honest and suggest transferring to human support

Response requirements:
- Use simple, easy-to-understand language
- Provide specific information and solutions
- If involving orders, please confirm the order number first
- If need to transfer to human, politely inform the user

Please respond in English.
"""

    def _build_user_prompt(
        self,
        user_message: str,
        intent: str,
        entities: dict,
        context: dict
    ) -> str:
        """构建用户提示词"""
        prompt = f"""
User message: {user_message}

Intent: {intent}
Entities: {entities}

Conversation context:
"""
        
        # 添加对话历史
        messages = context.get("messages", [])
        for msg in messages[-5:]:  # 最近5轮对话
            prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += "\nPlease generate an appropriate response."
        return prompt

    def _mock_generate_response(self, intent: str, language: str) -> str:
        """Mock生成回复"""
        responses = {
            "shipping_inquiry": {
                "en": "Thank you for your inquiry about shipping. Our standard shipping takes 7-15 business days to most countries. For faster delivery, we also offer express shipping options. May I have your order number so I can provide more specific information?",
                "zh": "感谢您咨询物流信息。我们的标准配送通常需要7-15个工作日送达大多数国家。我们也提供加急配送选项。请问您的订单号是多少?我可以为您提供更具体的信息。"
            },
            "order_status": {
                "en": "I'd be happy to help you check your order status. Could you please provide your order number? It usually starts with 'TK' followed by numbers.",
                "zh": "我很乐意帮您查询订单状态。请提供您的订单号,通常以'TK'开头后面跟着数字。"
            },
            "return_request": {
                "en": "I understand you'd like to return an item. We have a 30-day return policy for most products. To process your return request, I'll need your order number and the reason for return. Our team will review your request within 24 hours.",
                "zh": "我理解您想要退货。我们对大多数产品提供30天退货政策。为了处理您的退货请求,我需要您的订单号和退货原因。我们的团队将在24小时内审核您的请求。"
            },
            "product_inquiry": {
                "en": "Thank you for your interest in our products! I'd be happy to help you with product information. What specific details would you like to know?",
                "zh": "感谢您对我们产品的兴趣!我很乐意为您提供产品信息。您想了解哪些具体细节呢?"
            },
            "general_inquiry": {
                "en": "Hello! Thank you for contacting us. How may I assist you today?",
                "zh": "您好!感谢您联系我们。今天有什么可以帮助您的吗?"
            }
        }
        
        intent_responses = responses.get(intent, responses["general_inquiry"])
        return intent_responses.get(language, intent_responses.get("en", ""))

    def _get_fallback_response(self, language: str) -> str:
        """获取兜底回复"""
        if language == "zh":
            return "抱歉,我暂时无法回答您的问题。请稍后再试,或转接人工客服获得帮助。"
        else:
            return "I apologize, but I'm unable to answer your question at the moment. Please try again later or request to be transferred to human support for assistance."
