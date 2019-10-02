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
        _, items_page, total = tuple(map(lambda x: int(x), re.findall('\d+',text.replace(',', ''))))

        num_pages = total // items_page
        print('number of pages:', num_pages)

        urls = ['https://www.bestbuy.com/site/verizon/verizon-phones/pcmcat211300050002.c?cp={}&id=pcmcat211300050002'.format(x) for x in range(1,num_pages + 1)]

        for url in urls:
            # product list page
            yield Request(url = url, callback = self.parse_product_list)


    def parse_product_list(self, response):
        # product list
        rows=response.xpath('//ol[@class="sku-item-list"]/li')
        print(len(rows))
        print('=' * 50)
        for row in rows:
            url = row.xpath('.//div[@class="sku-title"]/h4/a/@href').extract_first()
            yield Request(url = 'https://www.bestbuy.com' + url,  callback = self.parse_product)

    def parse_product(self, response):
        # product first review page
        
        product = response.xpath('//div[@class="sku-title"]/h1/text()').extract_first()
        color = response.xpath('//li[@class="image selected"]/div/a/@title').extract_first()
        skuId = response.xpath('//div[@class="sku product-data"]/span[2]/text()').extract_first()  
        price = response.xpath('//li[@class="activated-pricing__option"][2]/button/span/span/text()').extract_first().replace(',','') 
        price = re.findall('[\d.,]+', price)[0].replace(',','')  
        model = response.xpath('//li[@class="text selected model family"]/div/a/@title').extract_first()       
        storage = response.xpath('//li[@class="text selected internal memory"]//span/text()').extract_first()
        review_url = response.xpath('//div[@class="see-all-reviews-button-container"]/a/@href').extract_first()
        meta = {
            'product':product,       
            'color': color,
            'skuId': skuId,
            'price': price,
            'model': model,
            'storage': storage
        }
        yield Request(url = "https://www.bestbuy.com" + review_url, meta = meta, callback = self.parse_review_pages)

    def parse_review_pages(self, response):
        nums = response.xpath('//div[@class="col-xs-6 col-sm-6"]/div/span[2]/text()').extract()
        reviews_page = re.findall('-(\d+)', nums[0].replace(',', ''))[0]
        total = nums[1].replace(',', '')  # 1,200 will raise exception
        num_pages = int(total)//int(reviews_page)+1
        print('total pages', num_pages)
        meta = {
                'product':response.meta['product'],       
                'color': response.meta['color'],
                'skuId': response.meta['skuId'],
                'price': response.meta['price'],
                'model': response.meta['model'],
                'storage': response.meta['storage']
                }
        first_url = response.xpath('//ul[@class="pagination ugc body-copy-lg"]/li/a/@href').extract_first().rsplit('page')[0]
        # https://www.bestbuy.com/site/reviews/google-pixel-3-xl-64gb-just-black-verizon/6303050?page=2
        urls = ['https://www.bestbuy.com{}page={}'.format(first_url, page) for page in range(1,num_pages+1)]
            
        for url in urls:
            #print(url)
            yield Request(url = url, meta = meta, callback = self.parse_review_detail)
    
    def parse_review_detail(self, response):
        reviews = response.xpath('//li[@class="review-item"]')
        print('reviews: ',len(reviews))
        for review in reviews:
            user = review.xpath('.//div[@class="visible-xs visible-sm ugc-author v-fw-medium body-copy-lg"]/text()').extract_first()            
            rating = review.xpath('.//div[@class="c-ratings-reviews v-medium"]/p/text()').extract_first()
            rating = re.findall('\d+', rating)[0]
            text = review.xpath('.//div[@class="ugc-review-body body-copy-lg"]/p/text()').extract_first()
            #print('review text {} bytes'.format(text))
            try:
                helpful = review.xpath('.//div[@class="feedback-display"]/button[1]/text()').extract()[1]
            except ValueError:
                helpful = ''

            try:
                unhelpful = review.xpath('.//div[@class="feedback-display"]/button[2]/text()').extract()[1]
            except ValueError:
                unhelpful = ''
            try:
                recommended = review.xpath('.//p[@class="v-fw-medium  ugc-recommendation"]/i/@class').extract_first().split('-')[1]
                recommended =['no','yes'][int(recommended=='confirm')]
            except:
                recommended = ''

            review_item = BestbuyProductItem()
            review_item['product'] = response.meta['product']
            review_item['color'] = response.meta['color']
            review_item['skuId'] = response.meta['skuId']
            review_item['price'] = response.meta['price']
            review_item['model'] = response.meta['model']
            review_item['storage'] = response.meta['storage']
            review_item['user'] = user
            review_item['helpful'] = helpful
            review_item['unhelpful'] = unhelpful
            review_item['rating'] = rating
            review_item['recommended'] = recommended
            review_item['text'] = text
            yield review_item

            


