"""Playwright automation engine for 1688 order processing."""

import asyncio
import logging
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.config import settings

logger = logging.getLogger(__name__)


class AlibabaAutomationEngine:
    """
    Playwright自动化引擎
    
    用于处理1688平台的自动化下单流程,包括:
    - 登录和会话保持
    - 商品页面导航
    - SKU选择
    - 收货地址填充
    - 订单提交
    - 反爬虫对抗
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.headless = getattr(settings, 'AUTOMATION_HEADLESS', True)
        self.mock_mode = getattr(settings, 'ALIBABA_MOCK_MODE', True)
        
        # 反检测配置
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        self.viewport = {"width": 1920, "height": 1080}

    async def initialize(self):
        """初始化浏览器"""
        if self.mock_mode:
            logger.info("[MOCK] Browser initialized")
            return

        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport=self.viewport,
            user_agent=self.user_agent,
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        # 注入反检测脚本
        await self._inject_stealth_scripts()
        
        self.page = await self.context.new_page()
        
        logger.info("Browser initialized successfully")

    async def _inject_stealth_scripts(self):
        """注入反检测脚本"""
        if not self.context:
            return

        await self.context.add_init_script("""
            // 隐藏webdriver属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 修改plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 修改languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
        """)

    async def login(self, username: str, password: str) -> bool:
        """
        登录1688
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否登录成功
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Logged in as {username}")
            return True

        if not self.page:
            logger.error("Browser not initialized")
            return False

        try:
            # 导航到登录页
            await self.page.goto("https://passport.1688.com/member/signin.htm")
            await self.page.wait_for_load_state("networkidle")

            # 填写登录表单
            await self.page.fill('input[name="username"]', username)
            await self.page.fill('input[name="password"]', password)

            # 点击登录按钮
            await self.page.click('button[type="submit"]')

            # 等待登录完成
            await asyncio.sleep(2)

            # 检查是否需要滑块验证
            if await self._check_slider_captcha():
                await self._handle_slider_captcha()

            # 验证登录状态
            await self.page.wait_for_url("**/www.1688.com/**", timeout=10000)
            
            logger.info("Login successful")
            return True

        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            return False

    async def place_order(
        self,
        product_url: str,
        sku_id: str,
        quantity: int,
        address: dict,
        remark: Optional[str] = None
    ) -> Optional[str]:
        """
        自动下单
        
        Args:
            product_url: 商品页面URL
            sku_id: SKU ID
            quantity: 数量
            address: 收货地址
            remark: 订单备注
            
        Returns:
            订单ID,失败返回None
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Order placed: {product_url}, qty={quantity}")
            return f"MOCK-ORDER-{sku_id}"

        if not self.page:
            logger.error("Browser not initialized")
            return None

        try:
            # 1. 导航到商品页面
            await self.page.goto(product_url)
            await self.page.wait_for_load_state("networkidle")

            # 2. 选择SKU
            await self._select_sku(sku_id)

            # 3. 设置数量
            await self._set_quantity(quantity)

            # 4. 点击立即订购
            await self.page.click('text=立即订购')
            await self.page.wait_for_load_state("networkidle")

            # 5. 填写收货地址
            await self._fill_address(address)

            # 6. 填写备注
            if remark:
                await self.page.fill('textarea[placeholder*="备注"]', remark)

            # 7. 提交订单
            await self.page.click('text=提交订单')
            await asyncio.sleep(2)

            # 8. 获取订单ID
            order_id = await self._extract_order_id()

            logger.info(f"Order placed successfully: {order_id}")
            return order_id

        except Exception as e:
            logger.error(f"Failed to place order: {e}", exc_info=True)
            return None

    async def _select_sku(self, sku_id: str):
        """选择SKU规格"""
        # TODO: 实现SKU选择逻辑
        # 需要根据SKU ID定位到对应的规格选项
        logger.info(f"Selecting SKU: {sku_id}")

    async def _set_quantity(self, quantity: int):
        """设置购买数量"""
        try:
            # 清空数量输入框
            await self.page.fill('input[type="number"]', str(quantity))
            logger.info(f"Set quantity to {quantity}")
        except Exception as e:
            logger.warning(f"Failed to set quantity: {e}")

    async def _fill_address(self, address: dict):
        """填写收货地址"""
        # TODO: 实现地址填充逻辑
        # 需要处理省市区三级联动选择
        logger.info(f"Filling address: {address.get('receiverName', '')}")

    async def _extract_order_id(self) -> str:
        """提取订单ID"""
        try:
            # 从页面URL或内容中提取订单ID
            url = self.page.url
            if "orderId=" in url:
                return url.split("orderId=")[1].split("&")[0]
            
            # 或从页面元素提取
            order_element = await self.page.query_selector('.order-id')
            if order_element:
                return await order_element.inner_text()
            
            return "UNKNOWN"
            
        except Exception as e:
            logger.error(f"Failed to extract order ID: {e}")
            return "UNKNOWN"

    async def _check_slider_captcha(self) -> bool:
        """检查是否出现滑块验证码"""
        try:
            slider = await self.page.query_selector('.slider-captcha')
            return slider is not None
        except Exception:
            return False

    async def _handle_slider_captcha(self):
        """处理滑块验证码"""
        # TODO: 实现滑块验证码识别和拖动
        # 可以集成第三方验证码识别服务
        logger.info("Handling slider captcha")

    async def save_session(self, filepath: str):
        """保存会话状态"""
        if self.context:
            await self.context.storage_state(path=filepath)
            logger.info(f"Session saved to {filepath}")

    async def load_session(self, filepath: str):
        """加载会话状态"""
        if self.browser:
            self.context = await self.browser.new_context(
                storage_state=filepath,
                viewport=self.viewport,
                user_agent=self.user_agent
            )
            self.page = await self.context.new_page()
            logger.info(f"Session loaded from {filepath}")

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

    async def take_screenshot(self, filepath: str):
        """截图"""
        if self.page:
            await self.page.screenshot(path=filepath)
            logger.info(f"Screenshot saved to {filepath}")

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        if self.mock_mode:
            return True

        if not self.page:
            return False

        try:
            await self.page.goto("https://www.1688.com")
            await self.page.wait_for_load_state("networkidle")

            # 检查是否存在登录用户名元素
            username_element = await self.page.query_selector('.username')
            return username_element is not None

        except Exception as e:
            logger.error(f"Failed to check login status: {e}")
            return False

    async def get_product_stock(self, product_url: str, sku_id: str) -> int:
        """获取商品库存"""
        if self.mock_mode:
            return 1000

        try:
            if not self.page:
                return 0

            await self.page.goto(product_url)
            await self.page.wait_for_load_state("networkidle")

            # 提取库存信息
            # TODO: 实现库存提取逻辑
            stock_element = await self.page.query_selector('.stock-count')
            if stock_element:
                stock_text = await stock_element.inner_text()
                return int(stock_text)

            return 0

        except Exception as e:
            logger.error(f"Failed to get stock: {e}")
            return 0
