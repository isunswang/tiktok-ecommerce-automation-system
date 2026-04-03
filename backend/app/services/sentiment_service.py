"""Sentiment analysis service for customer messages."""

import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Sentiment analysis service using GPT-4o."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = getattr(settings, 'llm_model', 'gpt-4o-mini')
        self.mock_mode = not settings.openai_api_key or getattr(settings, 'llm_mock_mode', True)

    async def analyze_sentiment(
        self,
        message: str,
        language: str = "en"
    ) -> dict:
        """
        分析情绪
        
        Args:
            message: 用户消息
            language: 语言代码
            
        Returns:
            {
                "sentiment": str,  # positive, neutral, negative
                "score": float,  # 0.0-1.0, 越低越负面
                "emotions": list[str],  # 具体情绪标签
                "urgency": str  # low, medium, high
            }
        """
        if self.mock_mode:
            return self._mock_analyze(message)

        try:
            # 构造提示词
            system_prompt = self._build_system_prompt(language)

            # 调用GPT-4o
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=200
            )

            # 解析响应
            result = self._parse_response(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}", exc_info=True)
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "emotions": [],
                "urgency": "low"
            }

    def _build_system_prompt(self, language: str) -> str:
        """构建系统提示词"""
        if language == "zh":
            return """
你是一个情绪分析专家。分析用户消息的情绪状态。

请以JSON格式返回:
{
  "sentiment": "positive/neutral/negative",
  "score": 0.5,
  "emotions": ["frustrated", "angry"],
  "urgency": "low/medium/high"
}

说明:
- sentiment: 总体情绪倾向
- score: 0.0-1.0, 0.0非常负面, 1.0非常正面
- emotions: 具体情绪标签,如frustrated, angry, happy, confused等
- urgency: 问题紧急程度,高紧急需要优先处理
"""
        else:
            return """
You are a sentiment analysis expert. Analyze the emotional state of user messages.

Please return in JSON format:
{
  "sentiment": "positive/neutral/negative",
  "score": 0.5,
  "emotions": ["frustrated", "angry"],
  "urgency": "low/medium/high"
}

Explanation:
- sentiment: Overall emotional tendency
- score: 0.0-1.0, 0.0 very negative, 1.0 very positive
- emotions: Specific emotion tags like frustrated, angry, happy, confused, etc.
- urgency: Issue urgency level, high urgency requires priority handling
"""

    def _parse_response(self, response: str) -> dict:
        """解析响应"""
        import json
        
        try:
            # 尝试提取JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            # 默认值
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "emotions": [],
                "urgency": "low"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse sentiment response: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "emotions": [],
                "urgency": "low"
            }

    def _mock_analyze(self, message: str) -> dict:
        """Mock情绪分析"""
        message_lower = message.lower()
        
        # 检测负面关键词
        negative_words = ["angry", "frustrated", "disappointed", "bad", "terrible", "awful", "complaint", "生气", "失望", "投诉"]
        positive_words = ["happy", "great", "excellent", "love", "amazing", "thank", "开心", "满意", "感谢"]
        
        negative_count = sum(1 for word in negative_words if word in message_lower)
        positive_count = sum(1 for word in positive_words if word in message_lower)
        
        if negative_count > positive_count:
            return {
                "sentiment": "negative",
                "score": 0.3,
                "emotions": ["frustrated", "disappointed"],
                "urgency": "high"
            }
        elif positive_count > negative_count:
            return {
                "sentiment": "positive",
                "score": 0.8,
                "emotions": ["happy", "satisfied"],
                "urgency": "low"
            }
        else:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "emotions": [],
                "urgency": "low"
            }

    async def should_transfer_to_human(
        self,
        sentiment_score: float,
        urgency: str,
        conversation_turns: int
    ) -> bool:
        """
        判断是否应该转人工
        
        Args:
            sentiment_score: 情绪评分
            urgency: 紧急程度
            conversation_turns: 对话轮次
            
        Returns:
            是否应该转人工
        """
        # 情绪评分过低
        if sentiment_score < 0.3:
            return True
        
        # 紧急程度高
        if urgency == "high":
            return True
        
        # 对话轮次过多仍未解决
        if conversation_turns > 10:
            return True
        
        return False

    async def batch_analyze_sentiments(
        self,
        messages: list[str],
        language: str = "en"
    ) -> list[dict]:
        """
        批量情绪分析
        
        Args:
            messages: 消息列表
            language: 语言代码
            
        Returns:
            情绪分析结果列表
        """
        results = []
        for message in messages:
            result = await self.analyze_sentiment(message, language)
            results.append(result)
        
        return results

    async def get_sentiment_trend(
        self,
        session_id: str
    ) -> dict:
        """
        获取会话的情绪趋势
        
        Args:
            session_id: 会话ID
            
        Returns:
            {
                "trend": str,  # improving, stable, declining
                "average_score": float
            }
        """
        # TODO: 从会话历史消息中分析情绪趋势
        # 这需要查询数据库中的消息记录
        
        return {
            "trend": "stable",
            "average_score": 0.5
        }
