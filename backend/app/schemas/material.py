"""Pydantic schemas for material management"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class MaterialBase(BaseModel):
    """素材基础模型"""
    product_id: UUID
    material_type: str  # "title", "description", "image", "video"
    language: str = "en"  # "en", "zh", "th", "vi", "id", "ms"
    content: str | None = None
    file_url: str | None = None
    metadata: dict | None = None


class MaterialCreate(MaterialBase):
    """创建素材"""
    pass


class MaterialResponse(MaterialBase):
    """素材响应"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MaterialTranslationRequest(BaseModel):
    """素材翻译请求"""
    text: str
    source_lang: str = "zh"
    target_lang: str = "en"
    context: str | None = None  # "title", "description", "bullet_point"


class MaterialTranslationResponse(BaseModel):
    """素材翻译响应"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float = Field(ge=0, le=1)
