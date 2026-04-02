"""Anomaly detection and alert management service."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.models.order import Order, OrderStatus
from app.models.fulfillment import PurchaseOrder, PurchaseOrderStatus

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Service for detecting anomalies and managing alerts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_order_anomalies(self, order_id: str) -> list[Alert]:
        """
        检测订单相关的异常
        
        Args:
            order_id: 订单ID
            
        Returns:
            检测到的告警列表
        """
        alerts = []

        # 获取订单
        order = await self._get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return alerts

        # 检测: 订单匹配失败
        if order.status == OrderStatus.MATCHING_FAILED:
            alert = await self._create_alert(
                alert_type=AlertType.ORDER_MATCHING_FAILED,
                severity=AlertSeverity.HIGH,
                title=f"Order {order.tiktok_order_id} matching failed",
                description="Unable to match order items to 1688 products",
                related_order_id=order.id
            )
            alerts.append(alert)

        # 检测: 价格异常
        price_anomaly = await self._check_price_anomaly(order)
        if price_anomaly:
            alert = await self._create_alert(
                alert_type=AlertType.ORDER_PRICE_ANOMALY,
                severity=AlertSeverity.MEDIUM,
                title=f"Price anomaly detected for order {order.tiktok_order_id}",
                description=price_anomaly,
                related_order_id=order.id
            )
            alerts.append(alert)

        # 检测: 履约延迟
        delay_days = await self._check_fulfillment_delay(order)
        if delay_days > 2:
            alert = await self._create_alert(
                alert_type=AlertType.FULFILLMENT_DELAY,
                severity=AlertSeverity.HIGH if delay_days > 3 else AlertSeverity.MEDIUM,
                title=f"Fulfillment delay for order {order.tiktok_order_id}",
                description=f"Order delayed by {delay_days} days",
                related_order_id=order.id
            )
            alerts.append(alert)

        return alerts

    async def detect_system_anomalies(self) -> list[Alert]:
        """
        检测系统级异常
        
        Returns:
            检测到的告警列表
        """
        alerts = []

        # 检测: 长时间待处理订单
        stale_orders = await self._get_stale_orders()
        if len(stale_orders) > 10:
            alert = await self._create_alert(
                alert_type=AlertType.SYSTEM_ERROR,
                severity=AlertSeverity.HIGH,
                title=f"Too many stale orders: {len(stale_orders)}",
                description="More than 10 orders pending for over 48 hours",
                alert_data={"order_count": len(stale_orders)}
            )
            alerts.append(alert)

        # 检测: 采购失败率
        failure_rate = await self._calculate_purchase_failure_rate()
        if failure_rate > 0.1:  # 失败率超过10%
            alert = await self._create_alert(
                alert_type=AlertType.PURCHASE_FAILED,
                severity=AlertSeverity.HIGH,
                title=f"High purchase failure rate: {failure_rate:.1%}",
                description="Purchase failure rate exceeds 10%",
                alert_data={"failure_rate": failure_rate}
            )
            alerts.append(alert)

        return alerts

    async def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: Optional[str] = None,
        related_order_id: Optional[str] = None,
        related_purchase_order_id: Optional[str] = None,
        related_supplier_id: Optional[str] = None,
        alert_data: Optional[dict] = None
    ) -> Alert:
        """创建告警"""
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            related_order_id=related_order_id,
            related_purchase_order_id=related_purchase_order_id,
            related_supplier_id=related_supplier_id,
            alert_data=alert_data,
            status=AlertStatus.OPEN
        )
        
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        
        logger.info(f"Created alert: {alert.id} - {title}")
        return alert

    async def acknowledge_alert(
        self, alert_id: str, user_id: Optional[str] = None
    ) -> Optional[Alert]:
        """确认告警"""
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await self.db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            logger.error(f"Alert {alert_id} not found")
            return None

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.assigned_to = user_id
        
        await self.db.commit()
        await self.db.refresh(alert)
        
        logger.info(f"Alert {alert_id} acknowledged by {user_id}")
        return alert

    async def resolve_alert(
        self,
        alert_id: str,
        resolution_note: str,
        user_id: Optional[str] = None
    ) -> Optional[Alert]:
        """解决告警"""
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await self.db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            logger.error(f"Alert {alert_id} not found")
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = user_id
        alert.resolution_note = resolution_note
        alert.resolved_at = datetime.utcnow().isoformat()
        
        await self.db.commit()
        await self.db.refresh(alert)
        
        logger.info(f"Alert {alert_id} resolved by {user_id}")
        return alert

    async def get_open_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50
    ) -> list[Alert]:
        """获取未解决的告警"""
        stmt = select(Alert).where(Alert.status == AlertStatus.OPEN)
        
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        
        stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_price_anomaly(self, order: Order) -> Optional[str]:
        """检查价格异常"""
        # TODO: 实现价格异常检测逻辑
        # 检查订单金额是否与历史订单或市场价差异过大
        return None

    async def _check_fulfillment_delay(self, order: Order) -> int:
        """检查履约延迟天数"""
        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            return 0

        # 计算订单创建时间到现在的天数
        created_at = datetime.fromisoformat(order.created_at) if isinstance(order.created_at, str) else order.created_at
        delay_days = (datetime.utcnow() - created_at).days
        
        return delay_days

    async def _get_stale_orders(self) -> list[Order]:
        """获取长时间待处理订单"""
        threshold = datetime.utcnow() - timedelta(hours=48)
        
        stmt = select(Order).where(
            and_(
                Order.status.in_([
                    OrderStatus.PENDING,
                    OrderStatus.MATCHED,
                    OrderStatus.MATCHING_FAILED
                ]),
                Order.created_at < threshold
            )
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _calculate_purchase_failure_rate(self) -> float:
        """计算采购失败率"""
        # 获取最近24小时的采购单
        threshold = datetime.utcnow() - timedelta(hours=24)
        
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.created_at >= threshold
        )
        result = await self.db.execute(stmt)
        purchase_orders = result.scalars().all()
        
        if not purchase_orders:
            return 0.0

        failed_count = sum(
            1 for po in purchase_orders
            if po.status == PurchaseOrderStatus.CANCELLED
        )
        
        return failed_count / len(purchase_orders)

    async def send_alert_notifications(self, alert: Alert) -> bool:
        """
        发送告警通知
        
        Args:
            alert: 告警对象
            
        Returns:
            是否发送成功
        """
        # TODO: 集成邮件、微信、短信通知
        # 根据alert.severity决定通知渠道
        
        logger.info(f"Sending notification for alert {alert.id}")
        
        # Mock: 标记为已发送
        alert.notification_sent = True
        alert.notification_channels = ["email"]
        
        await self.db.commit()
        
        return True
