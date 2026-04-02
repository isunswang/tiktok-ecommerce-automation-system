"""Material management API routes"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.material import (
    MaterialTranslationRequest,
    MaterialTranslationResponse,
    MaterialResponse
)
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/v1/materials", tags=["Materials"])


@router.post("/translate", response_model=MaterialTranslationResponse)
async def translate_text(
    request: MaterialTranslationRequest,
    current_user: User = Depends(get_current_user)
):
    """文本翻译接口"""
    translation_service = TranslationService()
    
    try:
        result = await translation_service.translate_text(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            context=request.context or "product_title"
        )
        
        return MaterialTranslationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/image-translate")
async def translate_image(
    image_file: UploadFile = File(...),
    target_lang: str = Form("en"),
    current_user: User = Depends(get_current_user)
):
    """图片翻译接口（OCR + 翻译 + 重绘）"""
    from app.services.image_translation_service import ImageTranslationService
    import tempfile
    import os
    
    # 保存上传的文件到临时目录
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        content = await image_file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        img_translation_service = ImageTranslationService()
        result = await img_translation_service.translate_image(
            image_path=tmp_path,
            target_lang=target_lang
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image translation failed: {str(e)}")
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/products/{product_id}/materials", response_model=list[MaterialResponse])
async def get_product_materials(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取商品的所有素材"""
    from sqlalchemy import select
    from app.models.material import Material
    from uuid import UUID
    
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    result = await db.execute(
        select(Material).where(Material.product_id == product_uuid)
    )
    materials = result.scalars().all()
    
    return [MaterialResponse.model_validate(m, from_attributes=True) for m in materials]


@router.post("/products/{product_id}/materials/generate")
async def generate_product_materials(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量生成商品素材（标题/描述翻译）"""
    from sqlalchemy import select
    from app.models.product import Product
    from uuid import UUID
    
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    # 查询商品
    result = await db.execute(select(Product).where(Product.id == product_uuid))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # TODO: 实现批量素材生成逻辑
    # 1. 提取商品标题/描述
    # 2. 调用翻译服务
    # 3. 保存到Material表
    # 4. 返回任务ID
    
    return {
        "task_id": "mock-task-id",
        "estimated_time": 60,
        "message": "Material generation started"
    }
