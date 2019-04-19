# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BestbuyProductItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    
    model = scrapy.Field()
    skuId = scrapy.Field()
    product = scrapy.Field()
    avg_rating = scrapy.Field()
    total_reviews = scrapy.Field()
    q_and_a = scrapy.Field()
    recommended = scrapy.Field()
    user = scrapy.Field()
    rating = scrapy.Field()
    helpful = scrapy.Field()
    unhelpful = scrapy.Field()

    