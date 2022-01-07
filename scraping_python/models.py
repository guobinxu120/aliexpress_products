#! -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, Float, Date, TIMESTAMP, String, Boolean, BigInteger, Text, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from . import settings

DeclarativeBase = declarative_base()


def db_connect():
    """Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance.
    """

    return create_engine(URL(**settings.DATABASE), connect_args={'charset': 'utf8', })

def create_tables(engine):
    """"""
    DeclarativeBase.metadata.create_all(engine)

class DB_Product_Data(DeclarativeBase):

    __tablename__ = 'product_data'

    ID = Column('id_pk', Integer, primary_key=True, autoincrement=True)

    product_id = Column('product_id', String(20))

    primary_category = Column('primary_category', String(128))
    sub_category = Column('sub_category', String(128))
    product_title = Column('product_title', String(256))
    product_url = Column('product_url', String(256))
    price = Column('price', String(128))

    customer_reviews_star_rating = Column('customer_reviews_star_rating', Float)

    customer_reviews_amount = Column('customer_reviews_amount', Integer)
    orders_amount_qty = Column('orders_amount_qty', Integer)
    pieces_available_amount_qty = Column('pieces_available_amount_qty', Integer)
    wish_list_amount_qty = Column('wish_list_amount_qty', Integer)
    inventory_amount = Column('inventory_amount', Integer)

    video_url = Column('video_url', String(512))
    img_url_1 = Column('img_url_1', String(512))
    img_url_2 = Column('img_url_2', String(512))
    img_url_3 = Column('img_url_3', String(512))
    img_url_4 = Column('img_url_4', String(512))
    img_url_5 = Column('img_url_5', String(512))

    ships_from_all_options = Column('ships_from_all_options', String(50))
    ships_from_1 = Column('ships_from_1', String(50))
    ships_from_2 = Column('ships_from_2', String(50))
    ships_from_3 = Column('ships_from_3', String(50))

    shipping_method_estimated_delivery_1 = Column('shipping_method_estimated_delivery_1', String(50))
    shipping_method_carrier_1 = Column('shipping_method_carrier_1', String(50))

    shipping_method_estimated_delivery_2 = Column('shipping_method_estimated_delivery_2', String(50))
    shipping_method_carrier_2 = Column('shipping_method_carrier_2', String(50))

    shipping_method_estimated_delivery_3 = Column('shipping_method_estimated_delivery_3', String(50))
    shipping_method_carrier_3 = Column('shipping_method_carrier_3', String(50))

    shipping_method_estimated_delivery_4 = Column('shipping_method_estimated_delivery_4', String(50))
    shipping_method_carrier_4 = Column('shipping_method_carrier_4', String(50))

    store_name = Column('store_name', String(128))
    store_url = Column('store_url', String(128))
    positive_feedback = Column('positive_feedback', String(50))
    aliexpress_seller_since = Column('aliexpress_seller_since', String(50))

    detailed_seller_ratings_item_as_described = Column('detailed_seller_ratings_item_as_described', Float)
    detailed_seller_ratings_communication = Column('detailed_seller_ratings_communication', Float)
    detailed_seller_ratings_shipping_speed = Column('detailed_seller_ratings_shipping_speed', Float)

    feedback_history_1_month = Column('feedback_history_1_month', String(10))
    feedback_history_3_months = Column('feedback_history_3_months', String(10))
    feedback_history_6_months = Column('feedback_history_6_months', String(10))

    followers_count = Column('followers_count', Integer)
    # lawful_basis = Column('lawful_basis', Text())

    # TODO: Add columns to schema. Check schema is created correctly and also datetime-stamp is updated correctly for new rows and for updated rows.
    # created_at = timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
    # updated_at = timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    # For example...
    # created_at = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    # sqlalchemy does not correctly create schema for created_at using this statement. See https://stackoverflow.com/questions/33743379/sqlalchemy-timestamp-on-update-extra
    # updated_at = Column(TIMESTAMP, default=datetime.now(), nullable=False, onupdate=datetime.now())

    # Leave these rows commented out.
    # company_category_c = Column('company_category_c', String(255))
    # company_sic_code1_c = Column('company_sic_code1_c', String(255))
    # company_status_c = Column('company_status_c', String(255))
    # companies_house_url_c = Column('companies_house_url_c', String(255))
    # company_number_c = Column('company_number_c', String(255))
    # accounting_reference_date_c = Column('accounting_reference_date_c', String(255))
    # company_incorporation_date_c = Column('company_incorporation_date_c', String(255))

    # __table_args__ = ( UniqueConstraint('ItemNumber', name='_item_number'), )
