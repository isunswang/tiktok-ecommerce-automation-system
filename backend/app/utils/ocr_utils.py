"""OCR工具封装，支持PaddleOCR和Tesseract"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR引擎封装"""
    
    def __init__(self, engine: str = "paddle", lang: str = "ch"):
        """
        初始化OCR引擎
        
        Args:
            engine: OCR引擎类型 ("paddle" 或 "tesseract")
            lang: 语言代码 ("ch", "en", etc.)
        """
        self.engine = engine
        self.lang = lang
        self.ocr_model = None
        self.tesseract = None
        
        if engine == "paddle":
            try:
                from paddleocr import PaddleOCR
                self.ocr_model = PaddleOCR(
                    use_angle_cls=True, 
                    lang=lang,
                    show_log=False
                )
                logger.info(f"PaddleOCR initialized with lang={lang}")
            except ImportError:
                logger.warning("PaddleOCR not installed, falling back to Tesseract")
                self.engine = "tesseract"
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}, falling back to Tesseract")
                self.engine = "tesseract"
        
        if self.engine == "tesseract":
            try:
                import pytesseract
                self.tesseract = pytesseract
                logger.info(f"Tesseract OCR initialized with lang={lang}")
            except ImportError:
                logger.error("Tesseract not installed. OCR functionality will be limited")
                raise RuntimeError("No OCR engine available. Please install PaddleOCR or Tesseract")
    
    def extract_text(self, image_path: str | Path) -> List[Dict[str, Any]]:
        """
        提取图片文字
        
        Args:
            image_path: 图片路径
            
        Returns:
            文字列表，每个元素包含:
            - text: 识别的文字
            - bbox: [x1, y1, x2, y2] 边界框坐标
            - confidence: 置信度 (0-1)
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if self.engine == "paddle":
            return self._extract_with_paddle(image_path)
        else:
            return self._extract_with_tesseract(image_path)
    
    def _extract_with_paddle(self, image_path: Path) -> List[Dict[str, Any]]:
        """PaddleOCR提取文字"""
        try:
            result = self.ocr_model.ocr(str(image_path), cls=True)
            
            texts = []
            if result and result[0]:
                for line in result[0]:
                    # PaddleOCR返回格式: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]
                    bbox_points = line[0]  # 四个角点
                    text = line[1][0]
                    confidence = float(line[1][1])
                    
                    # 转换为 [x1, y1, x2, y2] 格式
                    x_coords = [p[0] for p in bbox_points]
                    y_coords = [p[1] for p in bbox_points]
                    bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    
                    texts.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence
                    })
            
            logger.info(f"PaddleOCR extracted {len(texts)} text regions from {image_path}")
            return texts
            
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            raise
    
    def _extract_with_tesseract(self, image_path: Path) -> List[Dict[str, Any]]:
        """Tesseract提取文字"""
        try:
            img = Image.open(image_path)
            
            # 映射语言代码
            lang_map = {
                "ch": "chi_sim",  # 简体中文
                "en": "eng",
                "th": "tha",
                "vi": "vie",
                "id": "ind",
                "ms": "msa"
            }
            tesseract_lang = lang_map.get(self.lang, "eng")
            
            # 获取详细的文字数据
            data = self.tesseract.image_to_data(
                img, 
                lang=tesseract_lang,
                output_type=self.tesseract.Output.DICT
            )
            
            texts = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:
                    confidence = data['conf'][i]
                    # Tesseract置信度为-1到100，转换为0-1
                    conf = max(0, confidence / 100.0) if confidence > 0 else 0.0
                    
                    texts.append({
                        "text": text,
                        "bbox": [
                            data['left'][i], 
                            data['top'][i],
                            data['left'][i] + data['width'][i], 
                            data['top'][i] + data['height'][i]
                        ],
                        "confidence": conf
                    })
            
            logger.info(f"Tesseract extracted {len(texts)} text regions from {image_path}")
            return texts
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查OCR引擎是否可用"""
        return self.ocr_model is not None or self.tesseract is not None
