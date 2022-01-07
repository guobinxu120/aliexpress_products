# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import signals
import re
import io
from scraping_python.items import ProductItem
from sqlalchemy.orm import sessionmaker
from .models import DB_Product_Data, db_connect, create_tables


class DatabaseExportPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        # crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        Creates deals table.
        """
        engine = db_connect()
        create_tables(engine)
        self.Session = sessionmaker(bind=engine)

    def spider_opened(self, spider):
        spider.session = self.Session()

    def close_spider(self, spider):

        session = self.Session()
        session.close()

    def process_item(self, item, spider):
        """

        This method is called for every item pipeline component.

        """

        session = self.Session()
        record = DB_Product_Data(**item)

        if all(not value for value in item.values()):
            return item

        try:
            # if spider.name == 'aliexpress':
            instance = session.query(DB_Product_Data).filter_by(
                product_url=item.get("product_url", None),
                product_title=item["product_title"],
                price=item.get("price", None),
                primary_category=item.get("primary_category", None)).first()

            if not instance:
                session.add(record)
                session.commit()
            # else:
            #
            #     session.query(DB_Product_Data).filter_by(
            #         product_url=item.get("product_url", None),
            #         product_title=item["product_title"],
            #         price=item.get("price", None),
            #         primary_category=item.get("primary_category", None)
            #     ).update(dict(
            #         last_name=item.get("last_name"),
            #         lawful_basis_source_detail_c=item["lawful_basis_source_detail_c"],
            #         twitter_user_c=item.get("twitter_user_c"),
            #         date_reviewed=item["date_reviewed"],
            #         title=item.get("title", None),
            #         address=item.get("address", None),
            #         website_c=item.get("website_c"),
            #         description=item.get("description"),
            #         phone_work=item.get("phone_work"),
            #         phone_mobile=item.get("phone_mobile"),
            #         business_pillar_c=item["business_pillar_c"],
            #         target_data_source_c=item["target_data_source_c"],
            #         lawful_basis_source=item["lawful_basis_source"],
            #         lawful_basis=item["lawful_basis"],
            #         account_industry_c=item["account_industry_c"],
            #         account_type_c=item["account_type_c"]
            #
            #     ))
            #     session.commit()

        except:
            session.rollback()
            raise
        finally:
            session.close()

        return item