import re

import scrapy


class CozymealSpider(scrapy.Spider):
    name = 'cozymeal'
    allowed_domains = ['cozymeal.com']
    start_urls = [
        'http://www.cozymeal.com/austin/cooking-classes/'
    ]

    def parse(self, response):
        ## Get all cities
        city_list = response.css('.menu-level.first-level.cities-dropdown li.next-level a')
        for city in city_list:
            city_url = city.css('::attr(href)').get()
            city_name = city.css('::text').get()
            if '/cooking-classes' not in city_url:
                yield scrapy.Request('{}/cooking-classes'.format(city_url), callback=self.parse_single_city, meta={
                    'city': city_name,
                    'city_slug': city_url.replace('https://www.cozymeal.com/', '')
                })

    def parse_single_city(self, response):
        city = response.meta['city']
        city_slug = response.meta['city_slug']
        next_button = response.css('.pagination a[rel="next"]::attr(href)').get()

        if next_button:
            yield scrapy.Request(next_button)

        for meal in response.css('.panel-mealcard.new-tile-design'):
            class_url = meal.css('a[itemprop="url"]::attr(href)').get()

            meta = {
                'city': city,
                'city_slug': city_slug,
                'class_url': class_url,
                'description': meal.css('[itemprop="description"]::attr(content)').get(),
                'class_date__iso': meal.css('[itemprop="startDate"]::attr(content)').get(),
                'class_date': meal.css('[itemprop="startDate"]::text').get(),
                'scheduled': meal.css('[itemprop="eventStatus"]::attr(content)').get() == "https://schema.org/EventScheduled",
                'banner_text': meal.css('.ribbon::text').get(),
                'title': meal.css('.panel-body h3::text').get(),
                'class_type': meal.css('.panel-body .pull-left.text-primary::text').get(),
                'currency': meal.css('[itemprop="priceCurrency"]::attr(content)').get(),
                'price': meal.css('[itemprop="price"]::attr(content)').get(),
                'in_stock': meal.css('[itemprop="availability"]::attr(content)').get() == "http://schema.org/InStock",
                'sales_start': meal.css('[itemprop="validFrom"]::attr(content)').get(),
                'sales_end': meal.css('[itemprop="validThrough"]::attr(content)').get(),

                'chef_name': meal.css('[itemprop="performer"] [itemprop="name"]::text').get(),
                'chef_verified': meal.css('.mlc-verified-text::text').get() is not None,
                'location_name': meal.css('[itemprop="location"] [itemprop="name"]::text').get(),
                'location_area': meal.css('[itemprop="location"] [itemprop="addressLocality"]::text').get(),
                'in_person': meal.css('[itemprop="eventAttendanceMode"]::attr("content")').get() == "https://schema.org/OfflineEventAttendanceMode",

                'review_count': meal.css('.mlc-nb-reviews::text').get(),

                'chef_wears_mask': meal.css('[title="Chef Wearing a Mask"]').get() is not None,
                'social_distance_friendly': meal.css('[title="Social Distancing Friendly"]').get() is not None,
                'chef_provides_mask': meal.css('[title="Chef Providing Masks"]').get() is not None,

                'image_url': meal.css('[itemprop="image"]::attr(src)').get(),
            }

            yield scrapy.Request(class_url, callback=self.parse_class_page, meta={
                'data': meta
            })

    def parse_class_page(self, response):
        data = response.meta['data']

        data['about'] = response.css('[itemprop="offers"] .gray.font-small::text').get()
        data['can_request_date'] = response.xpath("//*[contains(text(), 'Request date')]").get() is not None

        data['location_neighborhood'] = response.css('#event-location .selected-date-address::text').get()

        data['long_description'] = response.css('#about .panel-body::text').get()
        menu = []
        all_menu_items = response.css('#menu .panel-body *')
        current_menu_item = current_menu_item = {}
        for menu_item_number, menu_item in enumerate(all_menu_items):
            text = menu_item.css('::text').get()
            if menu_item.root.tag == 'h4':
                # New item starting
                if menu_item_number > 0:
                    menu.append(current_menu_item)
                current_menu_item = {'title': text}
            else:
                current_menu_item['details'] = text

        data['menu'] = menu

        data['details'] = {}
        for detail_item in response.css('#details .panel-body ul li'):
            name = detail_item.css('.dtl-name::text').get()
            val = detail_item.css('.dtl-value::text').get()
            data['details'][name] = val

        yield data
