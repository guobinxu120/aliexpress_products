# -*- coding: utf-8 -*-
from scrapy import Spider, Request
from scrapy.loader import ItemLoader
from scrapy.utils.project import get_project_settings
from collections import OrderedDict
from datetime import datetime, timedelta
from scrapy.http import TextResponse
import requests, random, json, logging
from scraping_python.items import ProductItem

from scraping_python.models import DB_Product_Data

import re, time

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class aliexpressSpider(Spider):
    name = "aliexpress_with_http_proxy_and_5_min"
    start_url = 'https://www.aliexpress.com'
    domain1 = 'aliexpress.com'

    total_page_count = 1
    total_count = 0
    existing_data_list = []

    last_crawl_url = {}
    last_page = {}
    is_success = {}

    session = None

    crawl_status = ''
    connection = None
    cursor = None
    use_selenium = False


    item_ids_got_already = []

    # driver = webdriver.PhantomJS('phantomjs.exe')
    # driver.set_page_load_timeout(300)
    field_names = ['store_id', 'product_number', 'parent_product_number', 'is_variation',
                   'variation_theme', 'variation_value', 'upc',
                   'brand', 'mpn', 'model', 'detail_url', 'full_category_path',
                   'item_location_city', 'item_location_country', 'item_title',
                   'unit_price', 'shipping_cost', 'currency_code',
                   'description_text', 'description_html', 'specifics_html']
    # get static data from settings.py
    settings = get_project_settings()
    DIFF_BETWEEN_CATEGORIES = settings.get('DIFF_BETWEEN_CATEGORIES')
    SOCKET5_PROXY_HOST = settings.get('SOCKET5_PROXY_HOST')
    SOCKET5_PROXY_PORT = settings.get('SOCKET5_PROXY_PORT')
    TOTAL_COUNT_FOR_MOVING_OTHER_CATEGORY = settings.get('TOTAL_COUNT_FOR_MOVING_OTHER_CATEGORY')
    # list_proxy = settings.get('PROXIES')
    ###########################################################


    # proxy = random.choice(list_proxy)

    proxy_url = 'http://spys.me/proxy.txt'

    proxy_text = requests.get(proxy_url).text
    list_proxy_temp = proxy_text.split('\n')
    list_proxy = []
    for line in list_proxy_temp:
        if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
            ip = line.strip().split(':')[0].replace(' ', '')
            port = line.split(':')[-1].split(' ')[0]
            list_proxy.append('http://' + ip + ':' + port)
    proxy = random.choice(list_proxy)

    # setting for logging
    logger = logging.getLogger('aliexpress')
    hdlr = logging.FileHandler('log_for_aliexpress_products.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s %(levelname)s %(funcName)s() %(lineno)d:\t %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    #################################################################################



    category_index = 0
    start_second = 0
    cat_sub_data = []
    continue_item_count = 0


    def __init__(self, *args, **kwargs):
        super(aliexpressSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        # self.logger.info('Proxy (start): ' + self.proxy)

        yield Request(url=self.start_url,
                      callback=self.parse,
                      meta={
                          'proxy': self.proxy,
                            'method_string': 'parse',
                            'url': self.start_url},
                      errback=self.err_parse
                      )

    def parse(self, response):
        if 'https://login.' in response.url:
            self.logger.error('Error: login page found')
            self.err_parse(response)
            return

        if not self.cat_sub_data:
            main_cats_tags = response.xpath('//div[@class="categories-list-box"]/dl')

            for main_cats_tag in main_cats_tags:
                class_name = main_cats_tag.xpath('./@class').extract_first()
                class_name = class_name.split(' ')[-1].replace('cl-item-', '')

                main_menu_title = ''.join(main_cats_tag.xpath('./dt[@class="cate-name"]//text()').extract())

                url_for_sub_menu = 'https://www.aliexpress.com/api/load_ams_path.htm?path=aliexpress.com%2Fcommon%2F%40langField%2Fru%2Fc-{}-content.htm'.format(class_name)

                # response.meta['main_menu_title'] = main_menu_title
                # response.meta['method_string'] = 'parse_sub_menu'
                # response.meta['url'] = url_for_sub_menu
                # response.meta['proxy'] = self.proxy

                resp_sub_temp = requests.get(url_for_sub_menu)
                resp_sub = TextResponse(url=url_for_sub_menu,
                                body=resp_sub_temp.text,
                                encoding='utf-8')

                sub_cat_items = resp_sub.xpath('//dl[@class="sub-cate-items"]/dd/a')
                for sub_cat_item in sub_cat_items:
                    url_for_sub = sub_cat_item.xpath('./@href').extract_first()
                    sub_menu_title = sub_cat_item.xpath('./text()').extract_first()

                    # response.meta['sub_menu_title'] = sub_menu_title
                    # response.meta['method_string'] = 'parse_products'
                    # response.meta['url'] = response.urljoin(url_for_sub)
                    # response.meta['cat_id'] = url_for_sub.split('/category/')[-1].split('/')[0]
                    # response.meta['cat_url'] = response.urljoin(url_for_sub).split('?')[0]
                    # response.meta['next_page_index'] = 1
                    # response.meta['proxy'] = self.proxy

                    sub_data = {}
                    sub_data['url'] = response.urljoin(url_for_sub)
                    sub_data['main_menu_title'] = main_menu_title
                    sub_data['sub_menu_title'] = sub_menu_title
                    sub_data['cat_id'] = url_for_sub.split('/category/')[-1].split('/')[0]
                    sub_data['cat_url'] = response.urljoin(url_for_sub).split('?')[0]
                    sub_data['next_page_index'] = 1
                    self.cat_sub_data.append(sub_data)

        if self.category_index >= len(self.cat_sub_data):
            self.category_index = 0

        cat_sub_data_detail = self.cat_sub_data[self.category_index]
        response.meta['main_menu_title'] = cat_sub_data_detail.get('main_menu_title')
        response.meta['sub_menu_title'] = cat_sub_data_detail.get('sub_menu_title')
        response.meta['method_string'] = 'parse_products'
        response.meta['url'] = cat_sub_data_detail.get('url')
        response.meta['cat_id'] = cat_sub_data_detail.get('cat_id')
        response.meta['cat_url'] = cat_sub_data_detail.get('cat_url')
        response.meta['next_page_index'] = 1
        response.meta['proxy'] = self.proxy

        yield Request(url=cat_sub_data_detail.get('url'),
                      callback=self.parse_products,
                      meta=response.meta,
                      errback=self.err_parse,
                      dont_filter=True
                      )

        # for test
        # break
        ###########################

    def parse_products(self, response):
        if ('https://login.' in response.url) or ('location.href="https://login.aliexpress.com/' in response.text):
            ban_proxy = response.request.meta.get('proxy')
            if ban_proxy:
                ban_proxy = response.request.meta['proxy'].replace('http://', '')
            if ban_proxy in self.list_proxy:
                self.list_proxy.remove(ban_proxy)
            if len(self.list_proxy) < 1:
                proxy_text = requests.get(self.proxy_url).text
                list_proxy_temp = proxy_text.split('\n')
                self.list_proxy = []
                for line in list_proxy_temp:
                    if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
                        ip = line.strip().split(':')[0].replace(' ', '')
                        port = line.split(':')[-1].split(' ')[0]
                        self.list_proxy.append('http://' + ip + ':' + port)

            self.proxy = random.choice(self.list_proxy)
            # ban_proxy = response.meta.get('proxy')
            # if ban_proxy[2:] in self.proxy:
            #     self.proxy = random.choice(self.list_proxy)
            response.meta['proxy'] = self.proxy

            self.logger.error('Error: login page found')
            self.logger.info('Proxy (parse_products): ' + self.proxy)
            # print('Proxy (parse_products): ' + self.proxy)

            yield Request(url=response.urljoin(response.url),
                          callback=self.parse_products,
                          meta=response.meta,
                          errback=self.err_parse,
                          dont_filter=True)
            return
        products = re.findall('window.runParams = (.*?);', response.text)
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

                # for test
                # product_detail_url = 'https://www.aliexpress.com/item/32918228250.html'
                ############################

                response.meta['method_string'] = 'parse_product_detail'
                response.meta['url'] = response.urljoin(product_detail_url)
                response.meta['proxy'] = self.proxy

                yield Request(url=response.urljoin(product_detail_url),
                              callback=self.parse_product_detail,
                              meta=response.meta,
                              errback=self.err_parse)

                self.continue_item_count += 1

                if self.continue_item_count >= self.TOTAL_COUNT_FOR_MOVING_OTHER_CATEGORY:
                    break


                # for test
                # break
                ###########################

            if self.continue_item_count >= self.TOTAL_COUNT_FOR_MOVING_OTHER_CATEGORY:
                self.category_index += 1
                self.logger.info('Move next category!!! ')

                yield Request(url=self.start_url,
                              callback=self.parse,
                              meta={
                                  'proxy': self.proxy,
                                    'method_string': 'parse',
                                    'url': self.start_url},
                              errback=self.err_parse,
                              dont_filter=True
                              )
                return

            response.meta['next_page_index'] += 1
            next_page_index = response.meta.get('next_page_index')
            cat_id = response.meta.get('cat_id')
            cat_url = response.meta.get('cat_url')
            cat_name = cat_url.split('/')[-1].split('.')[0]
            next_url = '{}?trafficChannel=main' \
                       '&catName={}' \
                       '&CatId={}' \
                       '&ltype=wholesale&SortType=default' \
                       '&page={}&' \
                       'isrefine=y'.format(cat_url, cat_name, cat_id, str(next_page_index))

            response.meta['proxy'] = self.proxy
            yield Request(url=next_url,
                          callback=self.parse_products,
                          meta=response.meta,
                          errback=self.err_parse)
        else:
            self.category_index += 1
            self.logger.info('Move next category!!! ')

            yield Request(url=self.start_url,
                          callback=self.parse,
                          meta={'proxy': self.proxy,
                                'method_string': 'parse',
                                'url': self.start_url},
                          errback=self.err_parse,
                          dont_filter=True
                          )

    def parse_product_detail(self, response):
        if ('https://login.' in response.url) or ('location.href="https://login.aliexpress.com/' in response.text):
            ban_proxy = response.request.meta.get('proxy')
            if ban_proxy:
                ban_proxy = response.request.meta['proxy'].replace('http://', '')
            if ban_proxy in self.list_proxy:
                self.list_proxy.remove(ban_proxy)
            if len(self.list_proxy) < 1:
                proxy_text = requests.get(self.proxy_url).text
                list_proxy_temp = proxy_text.split('\n')
                self.list_proxy = []
                for line in list_proxy_temp:
                    if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
                        ip = line.strip().split(':')[0].replace(' ', '')
                        port = line.split(':')[-1].split(' ')[0]
                        self.list_proxy.append('http://' + ip + ':' + port)

            self.proxy = random.choice(self.list_proxy)
            # ban_proxy = response.meta.get('proxy')
            # if ban_proxy[2:] in self.proxy:
            #     self.proxy = random.choice(self.list_proxy)
            response.meta['proxy'] = self.proxy

            self.logger.error('Error: login page found')
            self.logger.info('Proxy (parse_product_detail): ' + self.proxy)
            # print('Proxy (parse_product_detail): ' + self.proxy)

            yield Request(url=response.url,
                          callback=self.parse_product_detail,
                          meta=response.meta,
                          errback=self.err_parse,
                          dont_filter=True)
            return
        product_json = {}

        script_text_list = response.xpath('//script/text()').extract()
        for s in script_text_list:
            if 'window.runParams =' in s:
                s = s.replace('\n', ' ').split('window.runParams = ')[-1]
                s = s.split('var GaData = {')[0].split('data:')[-1].split("csrfToken: '")[0].strip()
                s = s[:len(s) - 1]
                product_json = json.loads(s)
                break

        if not product_json:
            self.logger.info('There is no json data for product detail. So return')
            # print('There is no json data for product detail. So return')

            return

        titleModule = product_json.get('titleModule')
        actionModule = product_json.get('actionModule')

        priceModule = product_json.get('priceModule')
        feedbackRating = titleModule.get('feedbackRating')

        shippingModule = product_json.get('shippingModule')
        product_id = shippingModule.get('productId')

        commonModule = product_json.get('commonModule')

        if feedbackRating.get('totalValidNum') < 5:
            self.logger.info('The review count is less than 5(ProductID: {}). So return'.format(str(product_id)))
            # print('The review count is less than 5(ProductID: {}). So return'.format(str(product_id)))
            return

        quantityModule = product_json.get('quantityModule')

        imageModule = product_json.get('imageModule')
        imagePathList = imageModule.get('imagePathList')

        l = ItemLoader(item=ProductItem())

        l.add_value("product_id", str(product_id))
        l.add_value("primary_category", response.meta.get('main_menu_title'))
        l.add_value("sub_category", response.meta.get('sub_menu_title'))
        l.add_value("product_title", titleModule.get('subject'))
        l.add_value("product_url", response.url)
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
                self.logger.info('There is no price value(ProductID: {}). So return'.format(str(product_id)))
                # print('There is no price value(ProductID: {}). So return'.format(str(product_id)))

                return
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
            'referer': response.url
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
        # print('Total count: ' + str(self.total_count))

        l.load_item()
        yield l.load_item()

    def err_parse(self, response):
        ban_proxy = response.request.meta.get('proxy')
        if ban_proxy:
            ban_proxy = response.request.meta['proxy'].replace('http://', '')
        if ban_proxy in self.list_proxy:
            self.list_proxy.remove(ban_proxy)
        if len(self.list_proxy) < 1:
            proxy_text = requests.get(self.proxy_url).text
            list_proxy_temp = proxy_text.split('\n')
            self.list_proxy = []
            for line in list_proxy_temp:
                if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
                    ip = line.strip().split(':')[0].replace(' ', '')
                    port = line.split(':')[-1].split(' ')[0]
                    self.list_proxy.append('http://' + ip + ':' + port)

        self.proxy = random.choice(self.list_proxy)
        # ban_proxy = response.meta.get('proxy')
        # if ban_proxy[2:] in self.proxy:
        #     self.proxy = random.choice(self.list_proxy)

        self.logger.info('Method name: ' + response.request.meta['method_string'])
        self.logger.error('Because got login page by this proxy, another proxy should be selected.(Current proxy: {})'.format(ban_proxy))
        self.logger.info('Another Proxy selected: ' + self.proxy)
        # print ('Another Proxy: ' + self.proxy)

        response.request.meta['proxy'] = self.proxy

        method_string = response.request.meta['method_string']
        if not 'errpg' in response.request.url:
            if method_string == 'parse':
                yield Request(response.request.meta['url'],
                              callback=self.parse,
                              meta=response.request.meta,
                              dont_filter=True,
                              errback=self.err_parse)
            elif method_string == 'parse_sub_menu':
                yield Request(response.request.meta['url'],
                              callback=self.parse_sub_menu,
                              meta=response.request.meta,
                              dont_filter=True,
                              errback=self.err_parse)
            elif method_string == 'parse_products':
                yield Request(response.request.meta['url'],
                              callback=self.parse_products,
                              meta=response.request.meta,
                              dont_filter=True,
                              errback=self.err_parse)
            elif method_string == 'parse_product_detail':
                yield Request(response.request.meta['url'],
                              callback=self.parse_products,
                              meta=response.request.meta,
                              dont_filter=True,
                              errback=self.err_parse)