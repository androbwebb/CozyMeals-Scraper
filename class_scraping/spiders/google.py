import scrapy
import re
from scrapy.linkextractors import LinkExtractor

img_extensions = ['.png', '.jpg', '.jpeg', '.gif']
def is_image_link(text):
    return any([ext in text for ext in img_extensions])

class GoogleSpider(scrapy.Spider):
    name = 'google'
    allowed_domains = []
    start_urls = [
        'http://google.com/search?q=cooking+classes+austin',
        'http://google.com/search?q=sushi+making+class+austin',
        'http://google.com/search?q=cooking+class+restaurant+austin',
        'http://google.com/search?q=thai+cooking+classes+austin',
        'http://google.com/search?q=chinese+cooking+classes+austin',
    ]

    def parse(self, response):
        xlink = LinkExtractor()
        for link in xlink.extract_links(response):
            if 'google' not in link.url:
                yield scrapy.Request(link.url, callback=self.parse_sub_request, meta={'data': {
                    'url': link.url,
                    'text': link.text,
                }})

    def parse_sub_request(self, response):

        data = response.meta['data']
        data['text'] = response.css('title::text').get()
        raw_text = ''.join(response.xpath('//body//text()').extract()).replace('\n', '')
        data['emails_found'] = [x for x in re.findall(r'[\w\.-]+@[\w\.-]+', raw_text) if not is_image_link(x)]

        # These are kinda spammy, so I commented them out
        # data['raw_html'] = response.xpath('//*').get().replace('\n', '')
        # data['raw_text'] = raw_text
        yield data