# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst
import re


def clear_phone(value):

    if value is None:
        value = ""
    else:
        value = value.replace(" ", "")
        value = re.sub(r'^0+', "", value)
        if '+44' not in value:
            value = "+44" + value

    return value

def clear(value):

    if value is None:
        value = ""

    if isinstance(value, bytes):
        value = value.strip()

    if isinstance(value, str):
        value = value.strip()

    return value


class ProductItem(scrapy.Item):

    product_id = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    primary_category = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    sub_category = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    product_title = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    product_url = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    price = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    customer_reviews_star_rating = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    customer_reviews_amount = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    orders_amount_qty = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    pieces_available_amount_qty = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    wish_list_amount_qty = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    inventory_amount = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())

    video_url = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    img_url_1 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    img_url_2 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    img_url_3 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    img_url_4 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    img_url_5 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())

    ships_from_all_options = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    ships_from_1 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    ships_from_2 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    ships_from_3 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())

    shipping_method_estimated_delivery_1 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    shipping_method_carrier_1 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    shipping_method_estimated_delivery_2 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    shipping_method_carrier_2 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    shipping_method_estimated_delivery_3 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    shipping_method_carrier_3 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    shipping_method_estimated_delivery_4 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    shipping_method_carrier_4 = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())

    store_name = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    store_url = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    positive_feedback = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    aliexpress_seller_since = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    detailed_seller_ratings_item_as_described = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    detailed_seller_ratings_communication = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    detailed_seller_ratings_shipping_speed = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())

    feedback_history_1_month = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    feedback_history_3_months = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())
    feedback_history_6_months = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())

    followers_count = scrapy.Field(
        input_processor=MapCompose(clear),
        output_processor=TakeFirst())