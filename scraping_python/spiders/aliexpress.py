# -*- coding: utf-8 -*-
from scrapy import Spider, Request
from scrapy.loader import ItemLoader
from scrapy.utils.project import get_project_settings
from scrapy.http import TextResponse
from scraping_python.items import ProductItem
from scraping_python.models import DB_Product_Data

# import urllib2
import socks
import socket
import requests, random, json, logging, time
import re

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class aliexpressSpider(Spider):
    name = "aliexpress"

    start_url = 'https://www.aliexpress.com'
    # start_url = 'https://www.aliexpress.com/category/200003482/dresses.html?g=y'
    domain1 = 'aliexpress.com'

    total_count = 0
    session = None

    # get static data from settings.py
    settings = get_project_settings()
    DIFF_BETWEEN_CATEGORIES = settings.get('DIFF_BETWEEN_CATEGORIES')
    SOCKET5_PROXY_HOST = settings.get('SOCKET5_PROXY_HOST')
    SOCKET5_PROXY_PORT = settings.get('SOCKET5_PROXY_PORT')
    ###########################################################

    # setting for logging
    logger = logging.getLogger('aliexpress')
    hdlr = logging.FileHandler('log_for_aliexpress_products.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s %(levelname)s %(funcName)s() %(lineno)d:\t %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    #################################################################################

    session_re = requests.Session()

    def __init__(self, *args, **kwargs):
        super(aliexpressSpider, self).__init__(*args, **kwargs)

        socks.set_default_proxy(socks.SOCKS5, self.SOCKET5_PROXY_HOST, self.SOCKET5_PROXY_PORT)
        socket.socket = socks.socksocket

    def start_requests(self):
        yield Request(url=self.start_url,
                      callback=self.parse,
                      meta={'method_string': 'parse',
                            'url': self.start_url}
                      )

    def parse(self, response):
        main_cats_tags = response.xpath('//div[@class="categories-list-box"]/dl')
        while True:

            for main_cats_tag in main_cats_tags:
                go_next_category = False

                start_second = int(time.time())

                class_name = main_cats_tag.xpath('./@class').extract_first()
                class_name = class_name.split(' ')[-1].replace('cl-item-', '')

                main_menu_title = ''.join(main_cats_tag.xpath('./dt[@class="cate-name"]//text()').extract())

                self.logger.info('The category - {} started to scrape from {}'.format(main_menu_title, str(start_second)))

                url_for_sub_menu = 'https://www.aliexpress.com/api/load_ams_path.htm?path=aliexpress.com%2Fcommon%2F%40langField%2Fru%2Fc-{}-content.htm'.format(class_name)

                response.meta['main_menu_title'] = main_menu_title
                response.meta['method_string'] = 'parse_sub_menu'
                response.meta['url'] = url_for_sub_menu

                resp_main_temp = self.session_re.get(url_for_sub_menu)
                resp_main = TextResponse(url=url_for_sub_menu, body=resp_main_temp.text, encoding='utf-8')

                sub_cat_items = resp_main.xpath('//dl[@class="sub-cate-items"]/dd/a')
                for sub_cat_item in sub_cat_items:
                    url_for_sub = sub_cat_item.xpath('./@href').extract_first()
                    sub_menu_title = sub_cat_item.xpath('./text()').extract_first()

                    response.meta['sub_menu_title'] = sub_menu_title
                    response.meta['method_string'] = 'parse_products'
                    response.meta['url'] = response.urljoin(url_for_sub)
                    response.meta['cat_id'] = url_for_sub.split('/category/')[-1].split('/')[0]
                    response.meta['cat_url'] = response.urljoin(url_for_sub).split('?')[0]
                    response.meta['next_page_index'] = 1

                    # get product list
                    while True:
                        html = ''
                        while True:
                            resp_sub_temp = urllib2.urlopen(response.urljoin(url_for_sub))
                            html = resp_sub_temp.read()
                            if ('https://login.' in resp_sub_temp.url) or ('location.href="https://login.aliexpress.com/' in html):
                                time.sleep(5)
                            else:
                                break

                        products = re.findall('window.runParams = (.*?);', html)
                        products_data = {}
                        for product in products:
                            try:
                                products_data = json.loads(product)
                            except:
                                pass
                            if products_data:
                                break

                        if products_data:
                            items = products_data.get('items')
                            for item in items:
                                instance = self.session.query(DB_Product_Data).filter_by(
                                    product_id=item.get("productId", None)).first()

                                if instance:
                                    self.logger.info('This product id is existing. (product id: {})'.format(str(item.get("productId", None))))
                                    continue

                                product_detail_url = item.get('productDetailUrl')

                                # get product data
                                html_product = ''
                                while True:
                                    resp_product_temp = urllib2.urlopen(response.urljoin(product_detail_url))
                                    html_product = resp_product_temp.read()
                                    if ('https://login.' in resp_product_temp.url) or ('location.href="https://login.aliexpress.com/' in html_product):
                                        time.sleep(5)
                                    else:
                                        break

                                resp_product = TextResponse(url=response.urljoin(product_detail_url),
                                                            body=html_product,
                                                            encoding='utf-8')
                                product_json = {}

                                script_text_list = resp_product.xpath('//script/text()').extract()
                                for s in script_text_list:
                                    if 'window.runParams =' in s:
                                        s = s.replace('\n', ' ').split('window.runParams = ')[-1]
                                        s = s.split('var GaData = {')[0].split('data:')[-1].split("csrfToken: '")[0].strip()
                                        s = s[:len(s) - 1]
                                        product_json = json.loads(s)
                                        break

                                if not product_json:
                                    self.logger.info('There is no json data for product detail. So continue')
                                    continue

                                titleModule = product_json.get('titleModule')
                                actionModule = product_json.get('actionModule')

                                priceModule = product_json.get('priceModule')
                                feedbackRating = titleModule.get('feedbackRating')

                                shippingModule = product_json.get('shippingModule')
                                product_id = shippingModule.get('productId')

                                commonModule = product_json.get('commonModule')

                                if feedbackRating.get('totalValidNum') < 5:
                                    self.logger.info('The review count is less than 5(ProductID: {}). So continue'.format(str(product_id)))
                                    continue

                                quantityModule = product_json.get('quantityModule')

                                imageModule = product_json.get('imageModule')
                                imagePathList = imageModule.get('imagePathList')

                                l = ItemLoader(item=ProductItem())

                                l.add_value("product_id", str(product_id))
                                l.add_value("primary_category", response.meta.get('main_menu_title'))
                                l.add_value("sub_category", response.meta.get('sub_menu_title'))
                                l.add_value("product_title", titleModule.get('subject'))
                                l.add_value("product_url", response.urljoin(product_detail_url))
                                l.add_value("price", priceModule.get('formatedActivityPrice'))
                                l.add_value("customer_reviews_star_rating", float(feedbackRating.get('averageStar')))
                                l.add_value("customer_reviews_amount", feedbackRating.get('totalValidNum'))
                                l.add_value("orders_amount_qty", titleModule.get('tradeCount'))
                                l.add_value("pieces_available_amount_qty", quantityModule.get('totalAvailQuantity'))
                                l.add_value("wish_list_amount_qty", actionModule.get('itemWishedCount'))
                                l.add_value("inventory_amount", quantityModule.get('totalAvailQuantity'))

                                videoid = imageModule.get('videoId')
                                videoUid = imageModule.get('videoUid')
                                l.add_value("video_url", '')
                                if videoid:
                                    l.add_value("video_url", 'https://cloud.video.taobao.com/play/u/{}/p/1/e/6/t/10301/{}.mp4'.format(str(videoUid), str(videoid)))

                                for i, imagePath in enumerate(imagePathList):
                                    if i >= 5:
                                        break
                                    img_title = 'img_url_' + str(i + 1)
                                    l.add_value(img_title, imagePath)

                                l.add_value("ships_from_all_options", 'China')

                                skuModule = product_json.get('skuModule')
                                productSKUPropertyList = skuModule.get('productSKUPropertyList')
                                if productSKUPropertyList:
                                    for productSKUProperty in productSKUPropertyList:
                                        skuPropertyValues = productSKUProperty.get('skuPropertyValues')
                                        skuPropertyName = productSKUProperty.get('skuPropertyName')
                                        if skuPropertyName != 'Ships From':
                                            continue
                                        n = 1
                                        for skuPropertyValue in skuPropertyValues:
                                            propertyValueDisplayName = skuPropertyValue.get('propertyValueDisplayName')
                                            if propertyValueDisplayName == 'China':
                                                continue
                                            if n > 3:
                                                break
                                            ships_from_title = 'ships_from_' + str(n)

                                            l.add_value(ships_from_title, propertyValueDisplayName)
                                            n += 1

                                # get Shipping Method
                                try:
                                    maxActivityAmount = priceModule.get('maxActivityAmount').get('value')
                                    minActivityAmount = priceModule.get('minActivityAmount').get('value')
                                except:
                                    try:
                                        maxActivityAmount = priceModule.get('maxAmount').get('value')
                                        minActivityAmount = priceModule.get('minAmount').get('value')
                                    except:
                                        self.logger.info('There is no price value(ProductID: {}). So continue'.format(str(product_id)))
                                        continue

                                country_code = 'CA'
                                sellerAdminSeq = commonModule.get('sellerAdminSeq')
                                url_for_shipping = 'https://www.aliexpress.com/aeglodetailweb/api/logistics/freight' \
                                                   '?productId={}' \
                                                   '&count=1' \
                                                   '&minPrice={}' \
                                                   '&maxPrice={}' \
                                                   '&country={}' \
                                                   '&provinceCode=&cityCode=&tradeCurrency=USD' \
                                                   '&sellerAdminSeq={}' \
                                                   '&userScene=PC_DETAIL_SHIPPING_PANEL'.format(str(product_id),
                                                                                                str(minActivityAmount),
                                                                                                str(maxActivityAmount),
                                                                                                country_code,
                                                                                                str(sellerAdminSeq))

                                headers = {
                                    'referer': response.urljoin(product_detail_url)
                                }

                                resp_temp = requests.get(url_for_shipping, headers=headers)
                                shipping_method_data = {}
                                if resp_temp.status_code == 200:
                                    shipping_method_data = json.loads(resp_temp.text)
                                if shipping_method_data:
                                    body = shipping_method_data.get('body')
                                    freightResult = body.get('freightResult')
                                    for i, freightRe in enumerate(freightResult):
                                        if i >= 4:
                                            break
                                        time_val = freightRe.get('time')

                                        shipping_method_estimated_delivery_title = 'shipping_method_estimated_delivery_' + str(i + 1)
                                        l.add_value(shipping_method_estimated_delivery_title, time_val + ' days')

                                        shipping_method_carrier_title = 'shipping_method_carrier_' + str(i + 1)
                                        l.add_value(shipping_method_carrier_title, freightRe.get('company'))

                                storeModule = product_json.get('storeModule')
                                l.add_value('store_name', storeModule.get('storeName'))
                                l.add_value('store_url', storeModule.get('storeURL'))
                                l.add_value('positive_feedback', storeModule.get('positiveRate'))
                                l.add_value('aliexpress_seller_since', storeModule.get('openTime'))
                                l.add_value('followers_count', storeModule.get('followingNumber'))

                                url_for_store_feedback = 'https://feedback.aliexpress.com//display/evaluationDetail.htm' \
                                                         '?ownerMemberId={}' \
                                                         '&memberType=seller' \
                                                         '&callType=iframe' \
                                                         '&iframe_delete=true'.format(str(sellerAdminSeq))

                                resp_temp = requests.get(url_for_store_feedback)
                                resp = TextResponse(url=url_for_store_feedback,
                                                    body=resp_temp.text,
                                                    encoding='utf-8')
                                feedback_dsr = resp.xpath('//div[@id="feedback-dsr"]//table/tbody/tr')
                                for feedback in feedback_dsr:
                                    th_val = feedback.xpath('./th/text()').extract_first()
                                    val = feedback.xpath('./td/span[@class="dsr-text"]/em/text()').extract_first()
                                    if 'Item as Described' in th_val:
                                        l.add_value('detailed_seller_ratings_item_as_described', float(val))
                                    elif 'Communication' in th_val:
                                        l.add_value('detailed_seller_ratings_communication', float(val))
                                    elif 'Shipping Speed' in th_val:
                                        l.add_value('detailed_seller_ratings_shipping_speed', float(val))

                                feedback_history = resp.xpath('//div[@id="feedback-history"]//table/tbody/tr')
                                feedback_titles = []
                                for feedback in feedback_history:
                                    th_val = feedback.xpath('./th/text()').extract_first()
                                    if 'Feedback' in th_val:
                                        feedback_titles = feedback.xpath('./td/text()').extract()
                                    elif 'Positive feedback rate' in th_val:
                                        vals = feedback.xpath('./td/text()').extract()
                                        for j, feedback_title in enumerate(feedback_titles):
                                            val = vals[j]
                                            if '1 month' in feedback_title.lower():
                                                l.add_value('feedback_history_1_month', val)
                                            elif '3 months' in feedback_title.lower():
                                                l.add_value('feedback_history_3_months', val)
                                            elif '6 months' in feedback_title.lower():
                                                l.add_value('feedback_history_6_months', val)

                                self.total_count += 1

                                self.logger.info('Got product data(ProductID: {}).'.format(str(product_id)))
                                self.logger.info('Total count: ' + str(self.total_count))

                                l.load_item()
                                yield l.load_item()

                                end_second_of_product = int(time.time())
                                diff = end_second_of_product - start_second

                                self.logger.info('Passed for {} seconds.'.format(str(diff)))

                                if diff > self.DIFF_BETWEEN_CATEGORIES * 60:
                                    go_next_category = True
                                    break
                            if go_next_category:
                                break

                            # next page
                            response.meta['next_page_index'] += 1
                            next_page_index = response.meta.get('next_page_index')
                            cat_id = response.meta.get('cat_id')
                            cat_url = response.meta.get('cat_url')
                            cat_name = cat_url.split('/')[-1].split('.')[0]
                            url_for_sub = '{}?trafficChannel=main' \
                                       '&catName={}' \
                                       '&CatId={}' \
                                       '&ltype=wholesale&SortType=default' \
                                       '&page={}&' \
                                       'isrefine=y'.format(cat_url, cat_name, cat_id, str(next_page_index))
                            ####################################
                        else:
                            break
                    if go_next_category:
                        break