from scrapy import Spider
from bestbuy.items import BestbuyProductItem
from scrapy import Request
import re


class BestbuySpider(Spider):
    name = 'bestbuy_spider'
    #allowed_domains = ['https://www.bestbuy.com']
    allowed_domains = ['bestbuy.com']
    #https://www.bestbuy.com/site/searchpage.jsp?cp=1&searchType=search&browsedCategory=pcmcat209400050001&ks=960&sp=-bestsellingsort%20skuidsaas&sc=Global&list=y&usc=All%20Categories&type=page&id=pcat17071&iht=n&nrp=15&seeAll=&st=categoryid%24pcmcat209400050001&qp=carrier_facet%3DCarrier~Verizon
    #start_urls = ['https://www.bestbuy.com/site/laptop-computers/all-laptops/pcmcat138500050001.c?id=pcmcat138500050001']
    start_urls = ['https://www.bestbuy.com/site/verizon/verizon-phones/pcmcat211300050002.c?id=pcmcat211300050002']
    
    def parse(self, response):
        text = response.xpath('//div[@class="left-side"]/span/text()').extract_first()
        _, items_page, total = tuple(map(lambda x: int(x), re.findall('\d+',text)))

        num_pages = total // items_page
        #print('number of pages:', num_pages)

        urls = ['https://www.bestbuy.com/site/verizon/verizon-phones/pcmcat211300050002.c?cp={}&id=pcmcat211300050002'.format(x) for x in range(1,num_pages + 1)]
        for url in urls[:1]:
            # product list page
            yield Request(url = url, callback = self.parse_product_list)


    def parse_product_list(self, response):
        # product list
        rows=response.xpath('//ol[@class="sku-item-list"]/li')
        #print(len(rows))
       #print('=' * 50)
        for row in rows:
            url = row.xpath('.//div[@class="sku-title"]/h4/a/@href').extract_first()
            yield Request(url = 'https://www.bestbuy.com' + url,  callback = self.parse_options)

    def parse_options(self, response):
        rows = response.xpath('//div[@class="shop-product-variations"]')
        
        for row in rows[1:]:
            url = row.xpath('.//a/@href').extract_first()
            
            yield Request(url = url,  callback = self.parse_product)

    

    def parse_product(self, response):
        product = response.xpath('//div[@class="sku-title"]/h1/text()').extract_first()
        color = response.xpath('li[@class="image selected"]/div/a/@title').extract_first()
        skuId = response.xpath('//div[@class="sku product-data"]/span[2]/text()').extract_first()  
        price = response.xpath('//li[@class="activated-pricing__option"][2]/button/span/span/text()').extract_first().replace(',','') 
        price = re.findall('[\d.]+', price)[0]  
        model = response.xpath('//li[@class="text selected model family"]/div/a/@title').extract_first()       
        storage = response.xpath('//li[@class="text selected internal memory"]//span/text()').extract_first()
        print('product: {}'.format(product))
        print('colors: {}'.format(colors))
        print('skuId: {}'.format(skuId))
        print('price: {}'.format(price))
        review_url = response.xpath('//div[@class="see-all-reviews-button-container"]/a/@href').extract_first()
        #meta = {'option':response.meta['option'], 'storage':storages[i]}
        meta ={ 
                'product': product,
                'model':   model, 
                'skuId':   skuId,
                'color':  color,
                'storage': storage,
                'price':   price
            }
        yield Request(url = "https://www.bestbuy.com" + review_url, meta=meta, callback = self.parse_review_detail)


    def parse_review_detail(self, response):
        reviews = response.xpath('//li[@class="review-item"]')
        print('reviews: {}'.format(len(reviews)))
        for review in reviews:
            user = review.xpath('.//div[@class="visible-xs visible-sm ugc-author v-fw-medium body-copy-lg"]/text()').extract_first()            
            rating = review.xpath('.//div[@class="c-ratings-reviews v-medium"]/p/text()').extract_first()
            rating = re.findall('\d+', rating)[0]
            review_text = review.xpath('.//div[@class="line-clamp"]/p/text()').extract_first()
            
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
            print('user: {}'.format(user))
            print('rating: {}'.format(rating))
            print('review_text: {}'.format(review_text))
            print('helpful: {}'.format(helpful))
            print('unhelpful: {}'.format(unhelpful))
            print('recommended: {}'.format(recommended))
            product_item = BestbuyProductItem()
            
            product_item['product'] = response.meta['product']
            product_item['model'] =   response.meta['model']
            product_item['skuId'] =   response.meta['skuId']
            product_item['color'] =  response.meta['color']
            product_item['storage'] = response.meta['storage']
            product_item['price'] =   response.meta['price']
            product_item['user'] = user
            product_item['text'] = review_text
            product_item['helpful'] = helpful
            product_item['unhelpful'] = unhelpful
            product_item['rating'] = rating
            product_item['recommended'] = recommended
            yield product_item
        



