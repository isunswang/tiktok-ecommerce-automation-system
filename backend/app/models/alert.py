"""Alert models for anomaly detection and notifications."""

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AlertType(StrEnum):
    """Types of alerts."""
    # 订单异常
    ORDER_MATCHING_FAILED = "order_matching_failed"  # 订单匹配失败
    ORDER_NO_SUPPLIER = "order_no_supplier"  # 无可用供应商
    ORDER_PRICE_ANOMALY = "order_price_anomaly"  # 价格异常
    ORDER_STOCK_SHORTAGE = "order_stock_shortage"  # 库存不足
    
    # 履约异常
    FULFILLMENT_DELAY = "fulfillment_delay"  # 履约延迟
    PURCHASE_FAILED = "purchase_failed"  # 采购失败
    LOGISTICS_EXCEPTION = "logistics_exception"  # 物流异常
    
    # 供应商异常
    SUPPLIER_INACTIVE = "supplier_inactive"  # 供应商不活跃
    SUPPLIER_QUALITY_ISSUE = "supplier_quality_issue"  # 质量问题
    SUPPLIER_PRICE_CHANGE = "supplier_price_change"  # 价格变动
    
    # 系统异常
    API_ERROR = "api_error"  # API错误
    SYSTEM_ERROR = "system_error"  # 系统错误


class AlertSeverity(StrEnum):
    """Alert severity levels."""
    LOW = "low"  # 低优先级,24小时内处理
    MEDIUM = "medium"  # 中优先级,4小时内处理
    HIGH = "high"  # 高优先级,1小时内处理
    CRITICAL = "critical"  # 紧急,立即处理


class AlertStatus(StrEnum):
    """Alert status."""
    OPEN = "open"  # 待处理
    ACKNOWLEDGED = "acknowledged"  # 已确认
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"  # 已解决
    IGNORED = "ignored"  # 已忽略


class Alert(Base):
    """Alert model for tracking anomalies and issues."""

    __tablename__ = "alerts"

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(20), default=AlertSeverity.MEDIUM, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=AlertStatus.OPEN, nullable=False, index=True
    )
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 关联对象
    related_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True, index=True
    )
    related_purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True, index=True
    )
    related_supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True, index=True
    )
    
    # 告警详情
    alert_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {
    #   "order_id": "xxx",
    #   "item_count": 3,
    #   "failed_items": ["item1", "item2"],
    #   "suggested_actions": ["action1", "action2"]
    # }
    
    # 处理信息
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # 通知状态
    notification_sent: Mapped[bool] = mapped_column(default=False, nullable=False)
    notification_channels: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # ["email", "wechat", "sms"]
    
    # 重试次数
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    def __repr__(self) -> str:
        return f"<Alert {self.alert_type} severity={self.severity}>"
