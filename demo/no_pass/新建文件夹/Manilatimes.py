import scrapy
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests



class ManilatimesSpider(scrapy.Spider):
    name = 'Manilatimes'
    allowed_domains = ['manilatimes.net']
    start_urls = ['https://www.manilatimes.net/' ]
    website_id = 186  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # 刘鼎谦的sql配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(ManilatimesSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        if re.match(r'https://www.manilatimes.net/', response.url):  # 匹配二级目录

            soup = BeautifulSoup(response.text, 'html.parser')
            menus = soup.select('div.tdb-menu-items-pulldown > ul >li >a')
            menus = menus[0:19]
            for menu in menus[:17]:
                url = 'https://www.manilatimes.net' + menu.get('href')
                yield scrapy.Request(url, callback=self.parse)

        if re.match(r'https://www.manilatimes.net/\S+/\S+/$', response.url):  # 匹配目录下的文章 (有二级目录
            soup = BeautifulSoup(response.text, 'html.parser')
            for i in soup.select('div.td-module-meta-info > h3 > a'):
                url = i.get('href')
                yield scrapy.Request(url, callback=self.parse)
        elif re.match(r'https://www.manilatimes.net/\S+/$', response.url):  # 匹配目录下的文章  （没有二级目录
            soup = BeautifulSoup(response.text, 'html.parser')
            for i in soup.select('div.td-module-meta-info > h3 > a'):
                url = i.get('href')
                yield scrapy.Request(url, callback=self.parse)

        if re.match(r'https://www.manilatimes.net/\d+/\d+/\d+/', response.url):  # 爬取文章
            item = DemoItem()
            soup = BeautifulSoup(response.text, 'html.parser')
            item['title'] = soup.select('div.wpb_wrapper > div >div > span')[-1].text
            item['category1'] = soup.select('div.wpb_wrapper > div >div > span')[-3].text
            item['category2'] = soup.select('div.wpb_wrapper > div >div > span')[-2].text

            t = soup.select_one('time').attrs['datetime']
            item['pub_time'] = t.split('T')[0] + " " + t.split('T')[1].split("+")[0]
            item['abstract'] = soup.find('p').text

            ss = ""
            for s in soup.select('#fb-root ~ p'):
                ss += s.text + r'\n'

            item['body'] = ss
            item['images'] = [i.attrs['data-src'] for i in soup.select('figure > img')]

            yield item


