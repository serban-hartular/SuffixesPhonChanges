import scrapy
import pandas as pd



class DoomScraper(scrapy.Spider):
    name = "doom"
    def start_requests(self):
        nouns_df = pd.read_csv('../data/substantive_plural.csv', encoding='utf-8', sep='\t')
        nouns = set(nouns_df['Noun'].to_list())
        urls = [f'https://doom.lingv.ro/cautare/?query={n}' for n in nouns]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        entries = response.css('entry')
        yield {'url':response.url, 'entries':[e.extract() for e in entries]}
