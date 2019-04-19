from scrapy import Spider
from bestbuy.items import BestbuyProductItem
from scrapy import Request
import re


class BestbuySpider(Spider):
    name = 'bestbuy_spider'
    #allowed_domains = ['https://www.bestbuy.com']
    allowed_domains = ['bestbuy.com']
    #start_urls = ['https://www.bestbuy.com/site/laptop-computers/all-laptops/pcmcat138500050001.c?id=pcmcat138500050001']
    start_urls = ['https://www.bestbuy.com/site/verizon/verizon-phones/pcmcat211300050002.c?id=pcmcat211300050002']
    
    def parse(self, response):
        text = response.xpath('//div[@class="left-side"]/span/text()').extract_first()
        _, items_page, total = tuple(map(lambda x: int(x), re.findall('\d+',text)))

        num_pages = total // items_page
        #print('number of pages:', num_pages)

        urls = ['https://www.bestbuy.com/site/verizon/verizon-phones/pcmcat211300050002.c?cp={}&id=pcmcat211300050002'.format(x) for x in range(1,num_pages + 1)]
        for url in urls:
            # product list page
            yield Request(url = url, callback = self.parse_product_list)


    def parse_product_list(self, response):
        # product list
        rows=response.xpath('//ol[@class="sku-item-list"]/li')
        #print(len(rows))
       #print('=' * 50)
        for row in rows:
            model = row.xpath('.//div[@class="sku-model"]/div[1]/span[2]/text()').extract_first()
            skuId = row.xpath('.//div[@class="sku-model"]/div[2]/span[2]/text()').extract_first()            
            text = row.xpath('.//div[@class="c-ratings-reviews v-small"]/p/text()').extract_first()
            avg_rating, _, total_reviews = tuple(re.findall('[\d.]+', text))
            meta = {'model':model, 'skuId':skuId, 'avg_rating':avg_rating, 'total_reviews':total_reviews}
            url = row.xpath('.//div[@class="sku-title"]/h4/a/@href').extract_first()
            yield Request(url = 'https://www.bestbuy.com' + url, meta=meta, callback = self.parse_product)

    def parse_product(self, response):
        # product first review page
        product = response.xpath('//div[@class="sku-title"]/h1/text()').extract_first()
        q_and_a = response.xpath('//div[@class="ugc-qna-stats ugc-stat"]/a/text()').extract_first()
        q_and_a = re.findall('\d+', q_and_a)[0]
        #print(product)
        #print(q_and_a)
        #print('='*50)

        review_url = response.xpath('//div[@class="see-all-reviews-button-container"]/a/@href').extract_first()

        meta ={
            'product':product, 
            'model':response.meta['model'], 
            'skuId':response.meta['skuId'], 
            'q_and_a':q_and_a, 
            'avg_rating':response.meta['avg_rating'],
            'total_reviews':response.meta['total_reviews']
            }
        yield Request(url = "https://www.bestbuy.com" + review_url, meta = meta, callback = self.parse_review_detail)


    def parse_review_detail(self, response):
        review_bars = response.xpath('//div[@class="rating-bars col-xs-5"]/ul/li')
        recommended = response.xpath('//div[@class="donut-percent"]/span/text()').extract_first()

        product_item = BestbuyProductItem()
        product_item['model'] = response.meta['model']
        product_item['skuId'] = response.meta['skuId']
        product_item['product'] = response.meta['product']
        product_item['q_and_a'] = response.meta['q_and_a']
        product_item['avg_rating'] = response.meta['avg_rating']
        product_item['total_reviews'] = response.meta['total_reviews']
        product_item['recommended'] = recommended
        
        
       
        reviews = response.xpath('//li[@class="review-item"]')
        for review in reviews:
            user = review.xpath('.//div[@class="visible-xs visible-sm ugc-author v-fw-medium body-copy-lg"]/text()').extract_first()            
            rating = review.xpath('.//div[@class="c-ratings-reviews v-medium"]/p/text()').extract_first()
            rating = re.findall('\d+', rating)[0]
            try:
                helpful = review.xpath('.//div[@class="feedback-display"]/button[1]/text()').extract()[1]
            except ValueError:
                helpful = ''

            try:
                unhelpful = review.xpath('.//div[@class="feedback-display"]/button[2]/text()').extract()[1]
            except ValueError:
                unhelpful = ''

            
            product_item['skuId'] = response.meta['skuId']
            product_item['user'] = user
            product_item['helpful'] = helpful
            product_item['unhelpful'] = unhelpful
            product_item['rating'] = rating

            yield product_item



