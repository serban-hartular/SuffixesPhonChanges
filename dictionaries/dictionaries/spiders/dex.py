import pickle

import scrapy
import pandas as pd



class DexScraper(scrapy.Spider):
    name = "dex"
    def start_requests(self):
        with open('../data/doom_nouns_sing.p', 'rb') as handle:
            nouns = pickle.load(handle)
        urls = [f'https://dexonline.ro/definitie/{n}' for n in nouns]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        items = response.xpath('//div[@class="meaning-relations"] | //h3[@class="tree-heading"]')
        entry = {}
        for item in items:
            if item.root.tag == 'h3': # it's a word heading
                heading = ''.join(item.css('::text').getall())
                plur = ''.join(item.css('span.tree-inflected-form').css('::text').getall())
                pos = ''.join(item.css('span.tree-pos-info').css('::text').getall())
                pos_index = heading.find(pos)
                heading = heading[:pos_index]
                if entry:
                    entry = {k:v.strip() for k,v in entry.items()}
                    yield entry
                entry = {'word':heading, 'pos':pos, 'related':''}
            else: # it's a word relations thing
                entry['related'] += ''.join(item.css('::text').getall())
        if entry:
            entry = {k: v.strip() for k, v in entry.items()}
            yield entry


