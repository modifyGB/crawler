import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class bicolstandardSpider(scrapy.Spider):
    name = 'bicolstandard'
    website_id = 491 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['http://www.bicolstandard.com/search']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_rht',
        'password' : 'dg_rht',
        'db' : 'dg_test'
    }

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('#main-wrapper .post-outer .thumb > a'):
            yield Request(i.attrs['href'],callback=self.parse1)
        
    def parse1(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text)
        item['title'] = html.select('.post-head > h1')[0].text
        if len(html.select('.breadcrumbs > span > a')) >= 2:
            item['category1'] = html.select('.breadcrumbs > span > a')[1].text
        if len(html.select('.breadcrumbs > span > a')) >= 3:
            item['category2'] = html.select('.breadcrumbs > span > a')[2].text
        item['body'] = ''
        flag = False
        for i in html.select('article div'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('.timestamp-link > span')[0].text)
        item['images'] = []
        for i in html.select('article img'):
            item['images'].append(i.attrs['src'])
        yield item
