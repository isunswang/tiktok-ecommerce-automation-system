"""Customer service API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services.intent_service import IntentClassifier, IntentType
from app.services.faq_service import FAQService
from app.services.conversation_service import ConversationManager, ConversationState
from app.services.response_generator import ResponseGenerator
from app.services.sentiment_service import SentimentAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response schemas
class SendMessageRequest(BaseModel):
    """Send message request."""
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    buyer_id: str
    buyer_name: Optional[str] = None
    order_id: Optional[str] = None
    language: str = "en"


class MessageResponse(BaseModel):
    """Message response."""
    session_id: str
    response: str
    intent: str
    confidence: float
    should_transfer: bool
    faq_matched: Optional[bool] = None


class CreateSessionRequest(BaseModel):
    """Create session request."""
    buyer_id: str
    buyer_name: Optional[str] = None
    order_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response."""
    session_id: str
    status: str
    ai_resolved: bool


# Initialize services
intent_classifier = IntentClassifier()
response_generator = ResponseGenerator()
sentiment_analyzer = SentimentAnalyzer()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new customer service session."""
    conversation_manager = ConversationManager(db)
    
    session = await conversation_manager.create_session(
        buyer_id=request.buyer_id,
        buyer_name=request.buyer_name,
        order_id=request.order_id
    )
    
    return SessionResponse(
        session_id=str(session.id),
        status=session.status,
        ai_resolved=session.ai_resolved
    )


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response."""
    conversation_manager = ConversationManager(db)
    faq_service = FAQService(db)
    
    # 创建或获取会话
    if request.session_id:
        session = await conversation_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = await conversation_manager.create_session(
            buyer_id=request.buyer_id,
            buyer_name=request.buyer_name,
            order_id=request.order_id
        )
    
    # 保存用户消息
    from app.models.customer_service import CSMessageRole
    await conversation_manager.add_message(
        session_id=str(session.id),
        role=CSMessageRole.BUYER,
        content=request.message
    )
    
    # 获取对话上下文
    context = await conversation_manager.get_conversation_context(str(session.id))
    
    # 1. 意图识别
    intent_result = await intent_classifier.classify_intent(
        message=request.message,
        context=context,
        language=request.language
    )
    
    intent = intent_result.get("intent", IntentType.UNKNOWN)
    confidence = intent_result.get("confidence", 0.0)
    entities = intent_result.get("entities", {})
    
    logger.info(f"Intent: {intent}, Confidence: {confidence}")
    
    # 2. 尝试匹配FAQ
    faq = await faq_service.match_faq_by_rules(request.message)
    if faq:
        # 使用FAQ答案
        response = await response_generator.generate_faq_response(faq, request.language)
        await faq_service.increment_view_count(str(faq.id))
        faq_matched = True
    else:
        # 3. 生成AI回复
        response = await response_generator.generate_response(
            user_message=request.message,
            intent=intent,
            entities=entities,
            context=context,
            language=request.language
        )
        faq_matched = False
    
    # 4. 情绪分析
    sentiment_result = await sentiment_analyzer.analyze_sentiment(
        message=request.message,
        language=request.language
    )
    
    sentiment_score = sentiment_result.get("score", 0.5)
    urgency = sentiment_result.get("urgency", "low")
    
    # 5. 判断是否需要转人工
    messages = context.get("messages", [])
    should_transfer = await sentiment_analyzer.should_transfer_to_human(
        sentiment_score=sentiment_score,
        urgency=urgency,
        conversation_turns=len(messages) // 2
    )
    
    # 6. 保存AI回复
    await conversation_manager.add_message(
        session_id=str(session.id),
        role=CSMessageRole.AI,
        content=response
    )
    
    # 7. 如果需要转人工,更新会话状态
    if should_transfer:
        await conversation_manager.escalate_to_human(
            session_id=str(session.id),
            reason=f"Sentiment score: {sentiment_score}, Urgency: {urgency}"
        )
    
    return MessageResponse(
        session_id=str(session.id),
        response=response,
        intent=intent,
        confidence=confidence,
        should_transfer=should_transfer,
        faq_matched=faq_matched
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session details."""
    conversation_manager = ConversationManager(db)
    
    session = await conversation_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=str(session.id),
        status=session.status,
        ai_resolved=session.ai_resolved
    )


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """End a session."""
    conversation_manager = ConversationManager(db)
    
    session = await conversation_manager.end_session(session_id, ai_resolved=True)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session ended", "session_id": session_id}


@router.post("/sessions/{session_id}/transfer")
async def transfer_to_human(
    session_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Transfer session to human agent."""
    conversation_manager = ConversationManager(db)
    
    session = await conversation_manager.escalate_to_human(
        session_id=session_id,
        reason=reason or "Manual transfer requested"
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session transferred to human", "session_id": session_id}


@router.get("/faqs")
async def search_faqs(
    query: str,
    category: Optional[str] = None,
    language: str = "en",
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """Search FAQs."""
    faq_service = FAQService(db)
    
    faqs = await faq_service.search_faq(
        query=query,
        category=category,
        language=language,
        limit=limit
    )
    
    return {
        "faqs": [
            {
                "id": str(faq.id),
                "category": faq.category,
                "question": faq.question_en if language == "en" else faq.question,
                "answer": faq.answer_en if language == "en" else faq.answer
            }
            for faq in faqs
        ]
    }
