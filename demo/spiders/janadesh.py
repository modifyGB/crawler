import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests


class JanaSpider(scrapy.Spider):
    name = 'janadesh'
    allowed_domains = ['www.janadesh.in']
    # start_urls = ['http://www.janadesh.in/']
    website_id = 1067  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def start_requests(self):
        soup = BeautifulSoup(requests.get('http://www.janadesh.in/').text, 'html.parser')
        for i in soup.select('.menu-list ul li a')[:-4]:
            meta = {'category1':i.text}
            if re.match('^http',i.get('href')):
                yield Request(url=i.get('href'), meta=meta)

    def __init__(self, time=None, *args, **kwargs):  # 文章列表只有 时分 没有年日月。
        super(JanaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):  # 文章列表只有 时分 没有年日月。
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('.page-title ~ div.row > div'):
            url=i.select_one('a').get('href')
            response.meta['images'] = [i.select_one('img').get('src')]
            yield Request(url,meta=response.meta,callback=self.parse_item)

    def parse_item(self, response):     # 具体文章里面时间藏在  tt = soup.find(attrs={'property':'og:updated_time'}).get('content')
        soup = BeautifulSoup(response.text, 'html.parser')
        tt = soup.find(attrs={'property':'og:updated_time'}).get('content')
        tt = tt.split('T')[0]+' '+tt.split('T')[1].split('+')[0]
        if self.time == None or Util.format_time3(tt) >= int(self.time):
            item = DemoItem()
            item['category1'] = response.meta['category1']
            item['category2'] = 'News Details'
            item['title'] = soup.select_one('.read-content h5').text
            item['pub_time'] = tt   # 文章列表只有 时分 没有年日月。
            item['images'] = response.meta['images']
            ss = ''
            for p in soup.select('.read-content p'):
                ss += p.text
                ss += '\n'
            item['body'] = ss
            item['abstract'] = soup.select('.read-content p')[0].text
            return item
        else:
            self.logger.info('时间截止')
