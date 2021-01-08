import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests


class MalayaSpider(scrapy.Spider):
    name = 'malaya'
    allowed_domains = ['malaya.com.ph']
    start_urls = ['https://malaya.com.ph/']
    website_id = 193  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(MalayaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = bs(response.text, 'html.parser')    # ‘https://malaya.com.ph/index.php/news/’ 这个目录下的文章动态加载。
        for i in soup.select('#menu-main_menu-1 a')[1:]:
            url = i.get('href')
            yield scrapy.Request(url, callback=self.parse_menu)

    def parse_menu(self, response):
        soup = bs(response.text, 'html.parser')
        allPages = soup.select_one('span.pages').text.split(' ')[-1] if soup.select_one('span.pages').text else None  # 翻页
        if allPages :
            for i in range(int(allPages)):
                url = response.url + 'page/' + str(i + 1) + '/'
                yield scrapy.Request(url, callback=self.parse_essay)
        else:
            yield scrapy.Request(response.url, callback=self.parse_essay)

    def parse_essay(self, response):
        soup = bs(response.text, 'html.parser')
        for i in soup.select('div.td-block-row h3 a'):  # 每页的文章
            url = i.get('href')
            yield scrapy.Request(url, callback=self.parse_item)

    def parse_item(self, response):
        soup = bs(response.text, 'html.parser')
        item = DemoItem()
        category = response.url.split('/')[-3].split('_')
        if len(category) == 3:
            item['category1'] = category[1]
            item['category2'] = category[2]
        else:
            item['category1'] = category[0]
            item['category2'] = category[1]

        item['title'] = soup.select_one('h1.entry-title').text

        item['pub_time'] = Util.format_time2(soup.select('span.td-post-date > time')[0].text)
        item['images'] = [i.get('data-src') for i in soup.select('div.td-post-content img')]
        item['abstract'] = soup.select('div.td-post-content > p')[0].text

        ss = ''
        for i in soup.select('div.td-post-content > p'):
            ss += i.text + r'\n'
        item['body'] = ss

        return item
