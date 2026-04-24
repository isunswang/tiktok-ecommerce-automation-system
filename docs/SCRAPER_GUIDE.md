# 1688爬虫使用指南

## 概述

1688爬虫已实现完整的架构，支持：
- **Mock模式**: 生成测试数据，无需真实爬取
- **HTTP模式**: 直接HTTP请求解析HTML
- **Playwright模式**: 浏览器渲染动态内容（需额外配置）
- **代理池支持**: 可配置代理池绕过IP限制
- **数据库存储**: 自动存储到PostgreSQL

## 文件结构

```
scraper/
├── scraper/
│   ├── spiders/
│   │   └── alibaba.py          # 核心爬虫实现
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── alibaba_parser.py    # HTML解析器
│   ├── pipelines/
│   │   ├── __init__.py         # 数据处理管道
│   │   └── database_pipeline.py # 数据库存储
│   ├── middlewares.py          # 中间件（UA、代理、限速）
│   ├── items.py                # 数据模型
│   └── settings.py             # 爬虫配置
├── output/                     # 输出目录
├── requirements.txt            # Python依赖
└── scrapy.cfg                  # Scrapy配置
```

## 快速开始

### 1. 安装依赖

```bash
cd scraper
pip install -r requirements.txt
```

### 2. 运行爬虫

#### Mock模式（测试）
```bash
# 生成20条模拟数据
scrapy crawl alibaba -a keyword="手机壳" -a mock_mode=true -o output/products.json
```

#### 真实爬取
```bash
# 搜索关键词，爬取5页
scrapy crawl alibaba -a keyword="手机壳" -a max_pages=5 -o output/products.json

# 爬取详情页
scrapy crawl alibaba -a keyword="手机壳" -a max_pages=3 -a crawl_details=true -o output/products.json

# 使用Playwright渲染（需要安装 playwright install）
scrapy crawl alibaba -a keyword="手机壳" -a use_playwright=true -o output/products.json
```

### 3. Python脚本运行

```python
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
process.crawl('alibaba', keyword='手机壳', max_pages=5, mock_mode=False)
process.start()
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词 | 必填 |
| `max_pages` | 最大爬取页数 | 5 |
| `mock_mode` | Mock数据模式 | false |
| `use_playwright` | 使用Playwright渲染 | false |
| `crawl_details` | 爬取商品详情页 | false |

## 输出数据格式

```json
{
  "source_url": "https://detail.1688.com/offer/123456.html",
  "product_id": "123456",
  "title": "商品标题",
  "price_range": "10.00-20.00",
  "min_price": 10.00,
  "max_price": 20.00,
  "sales_count": 1000,
  "supplier_name": "供应商名称",
  "supplier_id": "12345",
  "supplier_location": "广州",
  "min_order_qty": 10,
  "delivery_days": 2,
  "rating": 4.5,
  "main_image_url": "https://...",
  "image_urls": ["https://..."],
  "category": "类目",
  "sku_specs": [{"sku_id": "xxx", "price": "10.00", "stock": 100}],
  "crawled_at": "2024-04-24T06:17:13Z"
}
```

## 代理配置

### 环境变量方式
```bash
export PROXY_LIST='["http://proxy1:8080", "http://proxy2:8080"]'
export PROXY_API='https://your-proxy-api.com/get'
```

### settings.py配置
```python
PROXY_LIST = [
    "http://proxy1:8080",
    "http://proxy2:8080",
]
```

## 注意事项

1. **反爬机制**: 1688有严格的反爬机制，建议：
   - 使用代理池
   - 控制请求频率（已默认3秒）
   - 轮换User-Agent（已启用）

2. **Playwright模式**: 更稳定但更慢，用于动态内容：
   ```bash
   playwright install chromium
   ```

3. **数据库存储**: 需要后端服务运行，否则Pipeline会跳过存储

## 下一步

1. 配置代理池以支持大规模爬取
2. 实现增量爬取（只爬取新增/更新的商品）
3. 添加商品详情页的完整解析
4. 集成到Agent工作流中自动触发爬取
