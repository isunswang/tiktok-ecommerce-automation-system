"""Scrapy items for 1688 product data."""

import scrapy


class AlibabaProductItem(scrapy.Item):
    """1688商品数据Item."""

    source_url = scrapy.Field()            # 1688商品链接
    product_id = scrapy.Field()            # 1688商品ID
    title = scrapy.Field()                 # 商品标题
    price_range = scrapy.Field()           # 价格区间 "12.00-25.00"
    min_price = scrapy.Field()             # 最低价格(Decimal)
    max_price = scrapy.Field()             # 最高价格(Decimal)
    sales_count = scrapy.Field()           # 月销量
    supplier_name = scrapy.Field()         # 供应商名称
    supplier_id = scrapy.Field()           # 供应商ID
    supplier_location = scrapy.Field()     # 供应商所在地
    min_order_qty = scrapy.Field()         # 最低起批量
    delivery_days = scrapy.Field()         # 发货周期(天)
    rating = scrapy.Field()                # 评分
    main_image_url = scrapy.Field()        # 主图URL
    image_urls = scrapy.Field()            # 所有图片URL列表
    sku_specs = scrapy.Field()             # SKU规格JSON
    detail_html = scrapy.Field()           # 详情页HTML(用于后续解析)
    category = scrapy.Field()              # 商品类目
    crawled_at = scrapy.Field()            # 采集时间
