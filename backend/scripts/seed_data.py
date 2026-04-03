"""
测试数据种子脚本 - 为MVP演示注入完整的测试数据。

运行方式：
    cd backend
    python -m scripts.seed_data

注意：
    - 运行前确保 PostgreSQL 和 Redis 已启动
    - 脚本会先清空所有表数据再重新插入
    - 默认管理员账号: admin@tiktok-ops.com / admin123
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 确保所有模型被导入（用于metadata.create_all）
from app.models.base import Base
from app.models.user import User, Role
from app.models.product import Product, ProductSKU, ProductImage, Category, Supplier
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.fulfillment import PurchaseOrder, Shipment, Forwarder
from app.models.finance import FinanceRecord, ExchangeRate
from app.models.customer_service import CSSession, CSMessage, Ticket
from app.models.faq import FAQ
from app.core.security import hash_password
from app.config import get_settings

settings = get_settings()

# ========== 测试数据定义 ==========

CATEGORIES = [
    {"name": "电子产品", "level": 1},
    {"name": "手机配件", "level": 1},
    {"name": "家居生活", "level": 1},
    {"name": "运动户外", "level": 1},
    {"name": "美妆个护", "level": 1},
]

SUPPLIERS = [
    {"name": "深圳华强电子科技", "supplier_code": "HQ001", "contact_name": "张经理", "contact_phone": "13800138001", "location": "深圳市福田区华强北路", "rating": Decimal("4.8")},
    {"name": "义乌小商品贸易", "supplier_code": "YW002", "contact_name": "李总", "contact_phone": "13900139002", "location": "浙江义乌市国际商贸城", "rating": Decimal("4.5")},
    {"name": "广州美妆供应链", "supplier_code": "GZ003", "contact_name": "王经理", "contact_phone": "13700137003", "location": "广州市白云区化妆品产业园", "rating": Decimal("4.6")},
    {"name": "温州皮革制品厂", "supplier_code": "WZ004", "contact_name": "陈总", "contact_phone": "13600136004", "location": "浙江温州市鹿城区皮革城", "rating": Decimal("4.3")},
    {"name": "佛山家居制造有限公司", "supplier_code": "FS005", "contact_name": "刘经理", "contact_phone": "13500135005", "location": "广东佛山市顺德区家居产业园", "rating": Decimal("4.7")},
]

PRODUCTS = [
    {"name": "无线蓝牙耳机5.3", "description": "真无线蓝牙耳机，主动降噪，续航30小时", "cost_price": Decimal("35.00"), "sale_price": Decimal("29.99"), "supplier_idx": 0, "category_idx": 0, "status": "active", "score": Decimal("4.7")},
    {"name": "手机壳星空款", "description": "全包防摔手机壳，星空渐变色设计", "cost_price": Decimal("5.00"), "sale_price": Decimal("9.99"), "supplier_idx": 1, "category_idx": 1, "status": "listed", "score": Decimal("4.5")},
    {"name": "便携充电宝20000mAh", "description": "大容量移动电源，支持65W快充", "cost_price": Decimal("55.00"), "sale_price": Decimal("39.99"), "supplier_idx": 0, "category_idx": 0, "status": "active", "score": Decimal("4.8")},
    {"name": "LED护眼台灯", "description": "折叠式LED台灯，3档调光，USB充电", "cost_price": Decimal("25.00"), "sale_price": Decimal("24.99"), "supplier_idx": 4, "category_idx": 2, "status": "listed", "score": Decimal("4.4")},
    {"name": "运动水杯750ml", "description": "Tritan材质，防漏设计，带刻度", "cost_price": Decimal("8.00"), "sale_price": Decimal("12.99"), "supplier_idx": 1, "category_idx": 3, "status": "active", "score": Decimal("4.6")},
    {"name": "加厚瑜伽垫6mm", "description": "TPE材质，防滑耐磨，双面纹理", "cost_price": Decimal("18.00"), "sale_price": Decimal("22.99"), "supplier_idx": 1, "category_idx": 3, "status": "active", "score": Decimal("4.5")},
    {"name": "面膜补水套装10片", "description": "玻尿酸补水面膜，敏感肌可用", "cost_price": Decimal("12.00"), "sale_price": Decimal("15.99"), "supplier_idx": 2, "category_idx": 4, "status": "listed", "score": Decimal("4.9")},
    {"name": "口红礼盒6支装", "description": "丝绒雾面口红，6色套装", "cost_price": Decimal("22.00"), "sale_price": Decimal("29.99"), "supplier_idx": 2, "category_idx": 4, "status": "active", "score": Decimal("4.7")},
    {"name": "蓝牙音箱迷你款", "description": "小型便携蓝牙音箱，IPX7防水", "cost_price": Decimal("30.00"), "sale_price": Decimal("25.99"), "supplier_idx": 0, "category_idx": 0, "status": "active", "score": Decimal("4.3")},
    {"name": "数据线三合一1.5m", "description": "Type-C/安卓/苹果三合一快充线", "cost_price": Decimal("3.50"), "sale_price": Decimal("7.99"), "supplier_idx": 0, "category_idx": 1, "status": "listed", "score": Decimal("4.4")},
    {"name": "手机桌面支架", "description": "铝合金折叠手机支架，多角度调节", "cost_price": Decimal("10.00"), "sale_price": Decimal("14.99"), "supplier_idx": 0, "category_idx": 1, "status": "active", "score": Decimal("4.6")},
    {"name": "机械键盘RGB背光", "description": "87键青轴机械键盘，全键无冲", "cost_price": Decimal("45.00"), "sale_price": Decimal("49.99"), "supplier_idx": 0, "category_idx": 0, "status": "draft", "score": Decimal("4.8")},
    {"name": "超大鼠标垫80x30cm", "description": "细面锁边游戏鼠标垫", "cost_price": Decimal("8.00"), "sale_price": Decimal("11.99"), "supplier_idx": 1, "category_idx": 0, "status": "active", "score": Decimal("4.5")},
    {"name": "不锈钢保温杯500ml", "description": "316不锈钢内胆，12小时保温", "cost_price": Decimal("20.00"), "sale_price": Decimal("19.99"), "supplier_idx": 1, "category_idx": 2, "status": "listed", "score": Decimal("4.7")},
    {"name": "轻便跑步鞋", "description": "网面透气跑步鞋，缓震减震", "cost_price": Decimal("45.00"), "sale_price": Decimal("39.99"), "supplier_idx": 3, "category_idx": 3, "status": "active", "score": Decimal("4.4")},
    {"name": "专业篮球7号", "description": "PU材质室内外通用篮球", "cost_price": Decimal("25.00"), "sale_price": Decimal("29.99"), "supplier_idx": 1, "category_idx": 3, "status": "active", "score": Decimal("4.6")},
    {"name": "智能计数跳绳", "description": "无绳/有绳两用，LED计数显示", "cost_price": Decimal("10.00"), "sale_price": Decimal("15.99"), "supplier_idx": 1, "category_idx": 3, "status": "draft", "score": Decimal("4.3")},
    {"name": "可调节哑铃套装", "description": "5-25kg可调节哑铃，含收纳架", "cost_price": Decimal("80.00"), "sale_price": Decimal("89.99"), "supplier_idx": 4, "category_idx": 3, "status": "active", "score": Decimal("4.8")},
    {"name": "护肤精华套装", "description": "烟酰胺美白精华+维C抗氧精华", "cost_price": Decimal("30.00"), "sale_price": Decimal("35.99"), "supplier_idx": 2, "category_idx": 4, "status": "listed", "score": Decimal("4.6")},
    {"name": "法式香水50ml", "description": "花果香调，持久留香", "cost_price": Decimal("18.00"), "sale_price": Decimal("24.99"), "supplier_idx": 2, "category_idx": 4, "status": "active", "score": Decimal("4.5")},
    {"name": "指甲油套装12色", "description": "快干甲油，持久不脱色", "cost_price": Decimal("10.00"), "sale_price": Decimal("14.99"), "supplier_idx": 2, "category_idx": 4, "status": "active", "score": Decimal("4.2")},
    {"name": "16色眼影盘", "description": "大地色+亮片，哑光珠光混合", "cost_price": Decimal("8.00"), "sale_price": Decimal("12.99"), "supplier_idx": 2, "category_idx": 4, "status": "listed", "score": Decimal("4.7")},
    {"name": "棒球帽休闲款", "description": "纯棉可调节帽围", "cost_price": Decimal("6.00"), "sale_price": Decimal("9.99"), "supplier_idx": 3, "category_idx": 3, "status": "active", "score": Decimal("4.4")},
    {"name": "冬季加厚围巾", "description": "羊绒混纺，柔软亲肤", "cost_price": Decimal("15.00"), "sale_price": Decimal("19.99"), "supplier_idx": 3, "category_idx": 2, "status": "active", "score": Decimal("4.6")},
    {"name": "触屏手套", "description": "冬季保暖，支持触屏操作", "cost_price": Decimal("5.00"), "sale_price": Decimal("8.99"), "supplier_idx": 3, "category_idx": 2, "status": "draft", "score": Decimal("4.3")},
    {"name": "棉袜5双装", "description": "纯棉抗菌运动袜", "cost_price": Decimal("5.00"), "sale_price": Decimal("7.99"), "supplier_idx": 3, "category_idx": 2, "status": "listed", "score": Decimal("4.5")},
    {"name": "桌面收纳盒", "description": "多功能分层收纳，竹木材质", "cost_price": Decimal("12.00"), "sale_price": Decimal("16.99"), "supplier_idx": 4, "category_idx": 2, "status": "active", "score": Decimal("4.7")},
    {"name": "智能加湿器", "description": "超声波静音加湿器，3L大容量", "cost_price": Decimal("30.00"), "sale_price": Decimal("32.99"), "supplier_idx": 4, "category_idx": 2, "status": "active", "score": Decimal("4.4")},
    {"name": "排插6位带USB", "description": "新国标排插，6孔+3USB", "cost_price": Decimal("10.00"), "sale_price": Decimal("14.99"), "supplier_idx": 0, "category_idx": 2, "status": "active", "score": Decimal("4.6")},
]

# SKU规格选项
COLOR_OPTIONS = ["黑色", "白色", "红色", "蓝色", "粉色", "绿色", "紫色", "灰色"]
SIZE_OPTIONS = ["S", "M", "L", "XL", "均码"]

ORDER_STATUSES = ["pending", "matched", "confirmed", "purchased", "shipped", "delivered", "completed", "cancelled"]
ORDER_STATUS_WEIGHTS = [15, 10, 8, 7, 20, 15, 15, 10]

BUYER_NAMES = [
    "John Smith", "Emily Johnson", "Michael Brown", "Sarah Davis", "David Wilson",
    "Jessica Taylor", "Robert Anderson", "Ashley Thomas", "Daniel Jackson", "Amanda White",
    "Christopher Harris", "Stephanie Martin", "Matthew Thompson", "Jennifer Garcia", "Andrew Martinez",
    "Nicole Robinson", "Joshua Clark", "Samantha Rodriguez", "Ryan Lewis", "Elizabeth Lee",
    "Brandon Walker", "Megan Hall", "Kevin Allen", "Rachel Young", "Justin King",
    "Lauren Wright", "Tyler Scott", "Kayla Green", "Brian Baker", "Michelle Adams",
    "Alex Nguyen", "Patricia Hill", "Eric Campbell", "Deborah Mitchell", "Shawn Roberts",
    "Lisa Carter", "Jeffrey Phillips", "Hannah Evans", "Raymond Turner", "Diana Torres",
    "Gregory Parker", "Olivia Collins", "Frank Edwards", "Chelsea Stewart", "Patrick Flores",
]

FAQ_DATA = [
    {"category": "shipping", "question": "什么时候发货？", "answer": "我们会在您下单后1-3个工作日内安排发货。", "question_en": "When will my order be shipped?", "answer_en": "We will ship your order within 1-3 business days.", "keywords": ["发货", "出货", "ship", "delivery"], "match_rules": {"fuzzy_match": ["发货", "出货", "ship"]}},
    {"category": "shipping", "question": "运费怎么算？", "answer": "满$29免运费，未满$29收取$4.99运费。", "question_en": "How much is shipping?", "answer_en": "Free shipping on orders over $29, otherwise $4.99.", "keywords": ["运费", "邮费", "shipping", "freight"], "match_rules": {"fuzzy_match": ["运费", "邮费", "shipping"]}},
    {"category": "return", "question": "可以退货吗？", "answer": "收到商品7天内可以申请退换货，需保持商品完好。", "question_en": "Can I return the product?", "answer_en": "You can request a return within 7 days of receiving the product.", "keywords": ["退货", "退款", "return", "refund"], "match_rules": {"fuzzy_match": ["退货", "退款", "return"]}},
    {"category": "payment", "question": "支持哪些付款方式？", "answer": "支持信用卡、PayPal、TikTok Pay等支付方式。", "question_en": "What payment methods do you accept?", "answer_en": "We accept credit cards, PayPal, and TikTok Pay.", "keywords": ["付款", "支付", "payment", "pay"], "match_rules": {"fuzzy_match": ["付款", "支付", "payment"]}},
    {"category": "product", "question": "商品是正品吗？", "answer": "所有商品均为正规渠道采购的正品，请放心购买。", "question_en": "Are the products authentic?", "answer_en": "All products are sourced through official channels and are 100% authentic.", "keywords": ["正品", "真假", "authentic", "genuine"], "match_rules": {"fuzzy_match": ["正品", "真假", "authentic"]}},
    {"category": "shipping", "question": "大概几天能到？", "answer": "美国地区一般7-15个工作日送达，偏远地区可能需要更长时间。", "question_en": "How long does delivery take?", "answer_en": "US delivery typically takes 7-15 business days.", "keywords": ["几天", "时间", "多久", "delivery time"], "match_rules": {"fuzzy_match": ["几天", "多久", "delivery time"]}},
    {"category": "product", "question": "如何选择合适的尺码？", "answer": "请参考商品详情页的尺码表，如有疑问可联系客服获取建议。", "question_en": "How to choose the right size?", "answer_en": "Please refer to the size chart on the product page.", "keywords": ["尺码", "大小", "size", "fit"], "match_rules": {"fuzzy_match": ["尺码", "大小", "size"]}},
    {"category": "general", "question": "如何联系客服？", "answer": "您可以通过TikTok Shop内的在线聊天功能联系我们的客服团队。", "question_en": "How to contact customer service?", "answer_en": "You can reach us through the in-app chat on TikTok Shop.", "keywords": ["客服", "联系", "contact", "support"], "match_rules": {"fuzzy_match": ["客服", "联系", "contact"]}},
    {"category": "payment", "question": "可以修改订单吗？", "answer": "订单提交后暂不支持修改，您可以取消订单后重新下单。", "question_en": "Can I modify my order?", "answer_en": "Orders cannot be modified after submission. Please cancel and reorder.", "keywords": ["修改", "更改", "modify", "change order"], "match_rules": {"fuzzy_match": ["修改订单", "更改订单", "modify order"]}},
    {"category": "coupon", "question": "怎么使用优惠券？", "answer": "结算时在优惠券栏输入优惠码即可享受折扣。", "question_en": "How to use a coupon?", "answer_en": "Enter your coupon code at checkout to apply the discount.", "keywords": ["优惠券", "折扣", "coupon", "discount"], "match_rules": {"fuzzy_match": ["优惠券", "折扣", "coupon"]}},
]


async def seed_data():
    """注入完整的MVP测试数据。"""
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        # === 1. 清空所有数据（按外键依赖顺序）===
        tables_to_clean = [
            "order_status_history", "order_items", "orders",
            "cs_messages", "tickets", "cs_sessions",
            "shipments", "purchase_orders",
            "finance_records", "exchange_rates",
            "product_images", "product_skus", "products",
            "categories", "suppliers",
            "faqs", "alerts", "sku_mappings", "match_records",
            "users", "roles", "forwarders",
            "materials",
        ]
        for table in tables_to_clean:
            try:
                await session.execute(text(f'DELETE FROM "{table}"'))
            except Exception:
                pass
        await session.commit()
        print("已清空所有表数据")

        # === 2. 创建用户 ===
        admin = User(
            username="admin@tiktok-ops.com",
            hashed_password=hash_password("admin123"),
            nickname="系统管理员",
            role="admin",
            is_active=True,
        )
        operator = User(
            username="operator@tiktok-ops.com",
            hashed_password=hash_password("admin123"),
            nickname="运营人员",
            role="operator",
            is_active=True,
        )
        cs_agent = User(
            username="cs@tiktok-ops.com",
            hashed_password=hash_password("admin123"),
            nickname="客服小美",
            role="cs_agent",
            is_active=True,
        )
        session.add_all([admin, operator, cs_agent])

        # === 3. 创建角色 ===
        for role_name, display_name in [("admin", "管理员"), ("operator", "运营人员"), ("cs_agent", "客服"), ("finance", "财务")]:
            role = Role(name=role_name, display_name=display_name)
            session.add(role)
        await session.flush()

        # === 4. 创建分类 ===
        category_objs = []
        for cat_data in CATEGORIES:
            cat = Category(**cat_data)
            session.add(cat)
            category_objs.append(cat)
        await session.flush()

        # === 5. 创建供应商 ===
        supplier_objs = []
        for sup_data in SUPPLIERS:
            sup = Supplier(**sup_data)
            session.add(sup)
            supplier_objs.append(sup)
        await session.flush()

        # === 6. 创建商品 + SKU + 图片 ===
        product_objs = []
        for i, p_data in enumerate(PRODUCTS):
            supplier_id = supplier_objs[p_data["supplier_idx"]].id
            category_id = category_objs[p_data["category_idx"]].id
            product = Product(
                name=p_data["name"],
                description=p_data["description"],
                cost_price=p_data["cost_price"],
                sale_price=p_data["sale_price"],
                status=p_data["status"],
                score=p_data["score"],
                supplier_id=supplier_id,
                category_id=category_id,
                tiktok_product_id=f"TK_PROD_{i+1:04d}" if p_data["status"] == "listed" else None,
            )
            session.add(product)
            product_objs.append(product)
        await session.flush()

        # 为每个商品创建SKU和图片
        sku_count = 0
        img_count = 0
        for i, product in enumerate(product_objs):
            # SKU: 2-3个
            sku_num = random.choice([2, 2, 3, 3])
            colors = random.sample(COLOR_OPTIONS, min(sku_num, len(COLOR_OPTIONS)))
            for j, color in enumerate(colors[:sku_num]):
                sku = ProductSKU(
                    product_id=product.id,
                    sku_code=f"SKU-{i+1:03d}-{j+1:02d}",
                    specs={"color": color, "size": "均码"},
                    cost_price=product.cost_price + Decimal(random.randint(0, 5)),
                    sale_price=product.sale_price + Decimal(random.randint(0, 3)) if product.sale_price else None,
                    stock=random.randint(50, 500),
                    tiktok_sku_id=f"TK_SKU_{uuid.uuid4().hex[:8]}" if product.status == "listed" else None,
                )
                session.add(sku)
                sku_count += 1

            # 图片: 1-3张
            img_num = random.choice([1, 2, 2, 3])
            for k in range(img_num):
                img = ProductImage(
                    product_id=product.id,
                    url=f"https://picsum.photos/seed/prod{product.id.hex[:6]}{k}/400/400",
                    image_type="main" if k == 0 else "detail",
                    sort_order=k,
                )
                session.add(img)
                img_count += 1
        await session.flush()
        print(f"商品: {len(product_objs)}条, SKU: {sku_count}条, 图片: {img_count}条")

        # === 7. 创建订单 + 订单项 ===
        now = datetime.now(timezone.utc)
        order_objs = []
        order_item_count = 0
        for i in range(50):
            status = random.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0]
            days_ago = random.randint(0, 30)
            created_time = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            buyer = random.choice(BUYER_NAMES)

            order = Order(
                tiktok_order_id=f"TK{created_time.strftime('%Y%m%d')}{i+1:04d}",
                status=status,
                total_amount=Decimal(round(random.uniform(5.99, 299.99), 2)),
                currency="USD",
                buyer_name=buyer,
                buyer_phone=f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                shipping_address={
                    "name": buyer,
                    "street": f"{random.randint(100,9999)} {random.choice(['Main St', 'Oak Ave', 'Elm Blvd', 'Pine Rd', 'Maple Dr'])}",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "San Diego", "Dallas", "Austin"]),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "zip": f"{random.randint(10000,99999)}",
                    "country": "US",
                },
                tracking_number=f"YT{random.randint(100000000,999999999)}" if status in ("shipped", "delivered", "completed") else None,
                remark=random.choice(["", "", "", "请尽快发货", "需要发票", "生日礼物请包装"]) if random.random() < 0.3 else None,
            )
            # 手动设置 created_at
            order.created_at = created_time
            order.updated_at = created_time
            session.add(order)
            order_objs.append(order)
        await session.flush()

        # 为每个订单创建订单项
        for order in order_objs:
            item_count = random.choices([1, 2, 3], weights=[50, 35, 15], k=1)[0]
            selected_products = random.sample(product_objs, min(item_count, len(product_objs)))
            for prod in selected_products:
                qty = random.randint(1, 3)
                unit_price = prod.sale_price or Decimal("19.99")
                item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    product_name=prod.name,
                    sku_code=f"SKU-{random.randint(1,30):03d}-{random.randint(1,3):02d}",
                    quantity=qty,
                    unit_price=unit_price,
                    subtotal=unit_price * qty,
                )
                session.add(item)
                order_item_count += 1
        await session.flush()
        print(f"订单: {len(order_objs)}条, 订单项: {order_item_count}条")

        # === 8. 创建财务记录 ===
        finance_records = []
        for order in order_objs:
            if order.status == "cancelled":
                # 退款记录
                finance_records.append(FinanceRecord(
                    order_id=order.id, type="refund", amount=order.total_amount,
                    currency="USD", exchange_rate=Decimal("7.25"), cny_amount=order.total_amount * Decimal("7.25"),
                    description=f"订单 {order.tiktok_order_id} 退款",
                    site="US",
                ))
                continue

            # 收入记录
            finance_records.append(FinanceRecord(
                order_id=order.id, type="income", amount=order.total_amount,
                currency="USD", exchange_rate=Decimal("7.25"), cny_amount=order.total_amount * Decimal("7.25"),
                description=f"订单 {order.tiktok_order_id} 销售收入",
                site="US",
            ))

            # 成本记录（采购+物流）
            cost_ratio = random.uniform(0.3, 0.5)
            cost = order.total_amount * Decimal(str(round(cost_ratio, 2)))
            finance_records.append(FinanceRecord(
                order_id=order.id, type="cost", amount=cost,
                currency="CNY", exchange_rate=Decimal("1.000000"), cny_amount=cost,
                description=f"订单 {order.tiktok_order_id} 采购成本",
                site="CN",
            ))

            # 平台手续费 (约5%)
            if random.random() < 0.7:
                fee = order.total_amount * Decimal("0.05")
                finance_records.append(FinanceRecord(
                    order_id=order.id, type="fee", amount=fee,
                    currency="USD", exchange_rate=Decimal("7.25"), cny_amount=fee * Decimal("7.25"),
                    description=f"订单 {order.tiktok_order_id} 平台手续费",
                    site="US",
                ))

        # 额外的提现记录
        for _ in range(5):
            finance_records.append(FinanceRecord(
                type="withdrawal", amount=Decimal(round(random.uniform(500, 5000), 2)),
                currency="USD", exchange_rate=Decimal("7.25"), cny_amount=Decimal(round(random.uniform(3600, 36000), 2)),
                description="TikTok Shop 提现",
                site="US",
            ))

        for record in finance_records:
            session.add(record)
        await session.flush()
        print(f"财务记录: {len(finance_records)}条")

        # === 9. 创建采购单 ===
        purchase_orders = []
        shippable_orders = [o for o in order_objs if o.status in ("matched", "confirmed", "purchased", "shipped", "delivered", "completed")]
        for i, order in enumerate(shippable_orders[:10]):
            po_status = random.choice(["pending", "ordered", "shipped", "received"])
            po = PurchaseOrder(
                alibaba_order_id=f"1688_{random.randint(100000,999999)}",
                supplier_id=random.choice(supplier_objs).id,
                status=po_status,
                total_amount=Decimal(round(random.uniform(100, 5000), 2)),
                currency="CNY",
                linked_order_ids=[str(order.id)],
                tracking_number=f"SF{random.randint(1000000000,9999999999)}" if po_status in ("shipped", "received") else None,
            )
            po.created_at = order.created_at + timedelta(hours=random.randint(1, 24))
            session.add(po)
            purchase_orders.append(po)
        await session.flush()
        print(f"采购单: {len(purchase_orders)}条")

        # === 10. 创建发货单 ===
        shipments = []
        for i, po in enumerate(purchase_orders):
            ship_count = random.choices([1, 2], weights=[70, 30], k=1)[0]
            for j in range(ship_count):
                ship_status = random.choice(["pending", "in_transit", "delivered", "returned", "exception"])
                ship = Shipment(
                    purchase_order_id=po.id,
                    order_id=random.choice(order_objs).id if random.random() < 0.5 else None,
                    carrier=random.choice(["4PX", "Yanwen", "YunExpress", "Cainiao"]),
                    tracking_number=f"{random.choice(['YT', 'SF', 'YZ'])}{random.randint(1000000000,9999999999)}",
                    status=ship_status,
                    origin=random.choice(["深圳", "广州", "义乌", "温州"]),
                    destination=random.choice(["New York, US", "Los Angeles, US", "London, UK", "Tokyo, JP"]),
                    estimated_delivery=(now + timedelta(days=random.randint(7, 30))).strftime("%Y-%m-%d") if ship_status in ("pending", "in_transit") else None,
                    logistics_events=[
                        {"time": (now - timedelta(days=random.randint(1, 10))).isoformat(), "status": "包裹已揽收", "location": "深圳集运仓"},
                        {"time": (now - timedelta(days=random.randint(1, 7))).isoformat(), "status": "已到达中转站", "location": "香港"},
                        {"time": (now - timedelta(days=random.randint(1, 5))).isoformat(), "status": "国际运输中", "location": "国际航线"},
                    ] if ship_status in ("in_transit", "delivered") else [],
                )
                session.add(ship)
                shipments.append(ship)
        await session.flush()
        print(f"发货单: {len(shipments)}条")

        # === 11. 创建客服会话 + 消息 ===
        cs_sessions = []
        cs_messages = []
        cs_statuses = ["active"] * 5 + ["closed"] * 3 + ["escalated"] * 2
        for i in range(10):
            buyer = random.choice(BUYER_NAMES)
            session_status = cs_statuses[i]
            cs = CSSession(
                tiktok_conversation_id=f"conv_{uuid.uuid4().hex[:10]}",
                buyer_id=f"buyer_{uuid.uuid4().hex[:8]}",
                buyer_name=buyer,
                order_id=random.choice(order_objs).id if random.random() < 0.6 else None,
                status=session_status,
                ai_resolved=session_status == "closed",
            )
            cs.created_at = now - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            session.add(cs)
            cs_sessions.append(cs)
        await session.flush()

        # 为每个会话创建消息
        buyer_questions = [
            "Hi, when will my order ship?",
            "我什么时候能收到货？",
            "Can I change my address?",
            "这个商品还有库存吗？",
            "What's the return policy?",
            "I received a damaged item",
            "这个可以用优惠券吗？",
            "Where is my tracking number?",
            "Do you ship to Canada?",
            "产品质量怎么样？",
        ]
        ai_responses = [
            "Thank you for reaching out! Your order is being processed and will ship within 1-3 business days. You'll receive a tracking number once it ships.",
            "感谢您的咨询！您的订单正在处理中，预计1-3个工作日内发货。发货后您会收到物流单号。",
            "I'm sorry, but we cannot modify the shipping address after the order has been placed. You may cancel and reorder with the correct address.",
            "是的，目前该商品有充足库存，您可以放心下单。",
            "We offer a 7-day return policy for all items. Please keep the product in its original condition.",
            "We're sorry to hear about the damaged item. Could you please send us a photo of the damage? We'll arrange a replacement for you.",
            "本商品支持使用优惠券。请在结算页面输入您的优惠码即可享受折扣。",
            "您的物流单号已生成，请查看订单详情页面。货物正在运输中。",
            "Currently we only ship within the United States. We are working on expanding to other countries.",
            "我们的商品均为正规渠道采购的正品，质量经过严格把控，请您放心购买。",
        ]

        for cs_session in cs_sessions:
            msg_count = random.randint(2, 5)
            for j in range(msg_count):
                role = "buyer" if j % 2 == 0 else "ai"
                content = buyer_questions[j // 2] if role == "buyer" else ai_responses[j // 2]
                if j >= len(buyer_questions):
                    content = buyer_questions[j % len(buyer_questions)]
                if j >= len(ai_responses):
                    content = ai_responses[j % len(ai_responses)]

                msg = CSMessage(
                    session_id=cs_session.id,
                    role=role,
                    content=content,
                )
                msg.created_at = cs_session.created_at + timedelta(minutes=j * random.randint(1, 10))
                session.add(msg)
                cs_messages.append(msg)
        await session.flush()
        print(f"客服会话: {len(cs_sessions)}条, 消息: {len(cs_messages)}条")

        # === 12. 创建FAQ知识库 ===
        for faq_data in FAQ_DATA:
            faq = FAQ(**faq_data, status="active", priority=random.randint(0, 10))
            session.add(faq)
        await session.flush()
        print(f"FAQ: {len(FAQ_DATA)}条")

        # === 13. 创建汇率记录 ===
        exchange_rates = [
            ExchangeRate(base_currency="CNY", target_currency="USD", rate=Decimal("0.1380"), source="manual"),
            ExchangeRate(base_currency="CNY", target_currency="GBP", rate=Decimal("0.1090"), source="manual"),
            ExchangeRate(base_currency="CNY", target_currency="THB", rate=Decimal("4.8500"), source="manual"),
            ExchangeRate(base_currency="CNY", target_currency="VND", rate=Decimal("3450.00"), source="manual"),
        ]
        for er in exchange_rates:
            session.add(er)
        await session.flush()
        print(f"汇率记录: {len(exchange_rates)}条")

        # === 提交所有数据 ===
        await session.commit()

        print("\n" + "=" * 50)
        print("测试数据注入完成！")
        print("=" * 50)
        print(f"管理员账号: admin@tiktok-ops.com")
        print(f"管理员密码: admin123")
        print("=" * 50)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
