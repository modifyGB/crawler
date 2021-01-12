import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class UnivartaSpider(scrapy.Spider):
    name = 'univarta'
    allowed_domains = ['univarta.com']
    start_urls = ['http://univarta.com/']

    website_id = 1041  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }
    hindi_month = {
        'जनवरी': 'Jan',
        'फ़रवरी': 'Feb',
        'जुलूस': 'Mar',
        'अप्रैल': 'Apr',
        'मई': 'May',
        'जून': 'Jun',
        'जुलाई': 'Jul',
        'अगस्त': 'Aug',
        'सितंबर': 'Sept',
        'अक्टूबर': 'Oct',
        'नवंबर': 'Nov',
        'दिसंबर': 'Dec'
    }

    def start_requests(self):  # 二级目录稍有难度，翻页和parseitem都不难
        soup = BeautifulSoup(requests.get('http://univarta.com/').text, 'html.parser')
        for i in soup.select('#ctl00_category1_sectionmenu > li '):
            meta = {'category1': i.select_one('a').text, 'category2': None}
            yield Request(url='http://univarta.com'+i.select_one('a').get('href'), meta=meta)  # 一级目录给parse_essay
            try:
                for j in i.select('ul>li>a'):
                    meta['category2'] = j.text
                    yield Request(url='http://univarta.com'+j.get('href'), meta=meta)
            except:
                self.logger.info('No more category2!')
                continue

    def __init__(self, time=None, *args, **kwargs):
        super(UnivartaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.CatNewsFirst_FirstNews '):
            tt = i.select_one('h1 ~ span').text.split('|')[0].strip()
            pub_time = Util.format_time2(tt.split()[1]+' '+tt.split()[0]+' '+tt.split()[2])
            url = 'http://www.univarta.com/'+i.select_one('a').get('href')
            response.meta['title'] = i.select_one('a').text
            response.meta['pub_time'] = pub_time
            try:
                response.meta['images'] = [i.select_one('img').get('src')]
            except:
                response.meta['images'] = []
            response.meta['abstract'] =i.select_one('h1 ~ p').text
            if self.time is None or Util.format_time3(pub_time) >= int(self.time):
                yield Request(url=url, meta=response.meta,
                              callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
        if flag:
            try:
                nextPage = 'http://www.univarta.com/news/india' + soup.select_one('.jp-current ~ a').get('href', 'Next page no more')
                yield Request(nextPage, meta=response.meta, callback=self.parse)
            except:
                self.logger.info('Next page no more!')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = response.meta['abstract']
        item['body'] = soup.select_one('.storydetails p').text  # 一大段，没有换行  （再者，翻译之后的html标签和原网页的大同小异，要以源标签为参考）
        item['images'] = response.meta['images']
        item['category2'] = response.meta['category2']
        item['pub_time'] = response.meta['pub_time']
        # self.logger.info('item item item item item item item item item item item item')
        return item

