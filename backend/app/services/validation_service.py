"""Pre-order validation service for 1688 purchase."""

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mapping import SKUMapping
from app.models.product import Supplier

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating orders before 1688 purchase."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_before_purchase(
        self,
        sku_mapping_id: str,
        quantity: int,
        expected_price: Decimal
    ) -> dict:
        """
        下单前全面校验
        
        Args:
            sku_mapping_id: SKU映射ID
            quantity: 购买数量
            expected_price: 预期价格
            
        Returns:
            {
                "is_valid": bool,
                "errors": list[str],
                "warnings": list[str],
                "validated_data": dict
            }
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "validated_data": {}
        }

        # 获取SKU映射
        sku_mapping = await self._get_sku_mapping(sku_mapping_id)
        if not sku_mapping:
            result["is_valid"] = False
            result["errors"].append("SKU mapping not found")
            return result

        # 1. 库存校验
        stock_valid, stock_msg = await self._validate_stock(sku_mapping, quantity)
        if not stock_valid:
            result["is_valid"] = False
            result["errors"].append(stock_msg)

        # 2. 价格变动校验
        price_valid, price_msg = await self._validate_price(
            sku_mapping, expected_price
        )
        if not price_valid:
            result["warnings"].append(price_msg)

        # 3. 商品状态校验
        product_valid, product_msg = await self._validate_product_status(sku_mapping)
        if not product_valid:
            result["is_valid"] = False
            result["errors"].append(product_msg)

        # 4. 供应商校验
        supplier_valid, supplier_msg = await self._validate_supplier(sku_mapping)
        if not supplier_valid:
            result["is_valid"] = False
            result["errors"].append(supplier_msg)

        # 5. 采购限额校验
        limit_valid, limit_msg = await self._validate_purchase_limit(quantity)
        if not limit_valid:
            result["is_valid"] = False
            result["errors"].append(limit_msg)

        result["validated_data"] = {
            "alibaba_product_id": sku_mapping.alibaba_product_id,
            "alibaba_sku_id": sku_mapping.alibaba_sku_id,
            "supplier_id": str(sku_mapping.supplier_id) if sku_mapping.supplier_id else None,
            "current_price": sku_mapping.alibaba_price,
            "quantity": quantity
        }

        return result

    async def _validate_stock(
        self, sku_mapping: SKUMapping, quantity: int
    ) -> tuple[bool, str]:
        """验证库存充足性"""
        # TODO: 调用1688 API获取实时库存
        # Mock: 假设库存充足
        return True, "Stock sufficient"

    async def _validate_price(
        self, sku_mapping: SKUMapping, expected_price: Decimal
    ) -> tuple[bool, str]:
        """验证价格变动"""
        if not sku_mapping.alibaba_price:
            return True, "No reference price"

        # 计算价格变动比例
        price_diff = abs(sku_mapping.alibaba_price - expected_price) / expected_price
        
        # 价格变动超过5%触发警告
        if price_diff > Decimal("0.05"):
            return False, (
                f"Price changed by {price_diff:.1%}: "
                f"expected {expected_price}, current {sku_mapping.alibaba_price}"
            )

        return True, "Price stable"

    async def _validate_product_status(
        self, sku_mapping: SKUMapping
    ) -> tuple[bool, str]:
        """验证商品状态"""
        # TODO: 调用1688 API检查商品是否上架、是否被删除等
        # Mock: 假设商品状态正常
        return True, "Product status normal"

    async def _validate_supplier(
        self, sku_mapping: SKUMapping
    ) -> tuple[bool, str]:
        """验证供应商状态"""
        if not sku_mapping.supplier_id:
            return False, "No supplier associated"

        stmt = select(Supplier).where(Supplier.id == sku_mapping.supplier_id)
        result = await self.db.execute(stmt)
        supplier = result.scalar_one_or_none()

        if not supplier:
            return False, "Supplier not found"

        if supplier.status != "active":
            return False, f"Supplier status is {supplier.status}"

        return True, "Supplier valid"

    async def _validate_purchase_limit(self, quantity: int) -> tuple[bool, str]:
        """验证采购限额"""
        # 单次采购数量限制
        MAX_QUANTITY_PER_ORDER = 100
        
        if quantity > MAX_QUANTITY_PER_ORDER:
            return False, f"Quantity exceeds limit: {MAX_QUANTITY_PER_ORDER}"

        return True, "Quantity within limit"

    async def _get_sku_mapping(self, sku_mapping_id: str) -> Optional[SKUMapping]:
        """获取SKU映射"""
        stmt = select(SKUMapping).where(SKUMapping.id == sku_mapping_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def batch_validate(
        self,
        items: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """
        批量校验
        
        Args:
            items: [{"sku_mapping_id": str, "quantity": int, "expected_price": Decimal}, ...]
            
        Returns:
            (有效项列表, 无效项列表)
        """
        valid_items = []
        invalid_items = []

        for item in items:
            result = await self.validate_before_purchase(
                item["sku_mapping_id"],
                item["quantity"],
                item["expected_price"]
            )

            if result["is_valid"]:
                valid_items.append({
                    **item,
                    "validated_data": result["validated_data"]
                })
            else:
                invalid_items.append({
                    **item,
                    "errors": result["errors"],
                    "warnings": result["warnings"]
                })

        return valid_items, invalid_items

    async def check_price_fluctuation(
        self, alibaba_product_id: str, days: int = 7
    ) -> dict:
        """
        检查商品价格波动
        
        Args:
            alibaba_product_id: 1688商品ID
            days: 检查天数
            
        Returns:
            {
                "min_price": Decimal,
                "max_price": Decimal,
                "avg_price": Decimal,
                "fluctuation_rate": float
            }
        """
        # TODO: 从历史价格记录中分析波动
        # Mock: 返回假数据
        return {
            "min_price": Decimal("50.00"),
            "max_price": Decimal("60.00"),
            "avg_price": Decimal("55.00"),
            "fluctuation_rate": 0.18
        }
