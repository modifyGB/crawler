import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time
import requests


class FiliSpider(scrapy.Spider):
    name = 'fili'
    allowed_domains = ['filipinoexpress.com']
    start_urls = ['http://www.filipinoexpress.com/']
    website_id = 182  # 网站的id(必填)
    language_id = 2266  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(FiliSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time
    def parse(self, response):
        soup = bs(response.text, 'html.parser')
        for i in soup.select('#s5_nav > li.active ~li > span >span >a')[:5]:
            url = 'http://www.filipinoexpress.com' + i.get('href')
            yield scrapy.Request(url, callback=self.parse_menu)

    def parse_menu(self, response):
        soup = bs(response.text, 'html.parser')
        allPages = soup.select_one('li.pagination-end > a').get('href').split('=')[1]  # 翻页
        for i in range(int(int(allPages) / 10)):
            url = response.url + '?start=' + str(i * 10)
            yield scrapy.Request(url, callback=self.parse_essay)

    def parse_essay(self, response):
        soup = bs(response.text, 'html.parser')
        for i in soup.select('div.blog > div >div> h2 > a'):  # 每页的文章
            url = 'http://www.filipinoexpress.com' + i.get('href')
            yield scrapy.Request(url, callback=self.parse_item)

    def parse_item(self, response):
        soup = bs(response.text, 'html.parser')
        item = DemoItem()
        category = soup.select('div.breadcrumbs > a')
        if len(category) == 1:
            item['category1'] = category[0].text
            item['category2'] = None
        else:
            item['category1'] = category[0].text
            item['category2'] = category[1].text

        item['title'] = soup.select('div.breadcrumbs > span')[-1].text
        ttt = soup.select('dd.published')[0].text.split(',')[1].split(' ')[1:]
        datetime = ttt[2] + '-' + Util.month2[ttt[1]] + '-' + ttt[0] + ' ' + ttt[-1][:5] + ':00'
        item['pub_time'] = datetime
        item['images'] = None
        item['abstract'] = soup.select('div.item-page > p')[0].text

        ss = ''
        for i in soup.select('div.item-page > p'):
            ss += i.text + r'\n'
        item['body'] = ss

        yield item
