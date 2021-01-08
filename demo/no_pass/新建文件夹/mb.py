import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time
import requests


class MbSpider(scrapy.Spider):
    name = 'mb'
    allowed_domains = ['mb.com.ph']
    start_urls = ['https://mb.com.ph']
    website_id = 189  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(MbSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        if re.match(r'https://mb.com.ph$', response.url):  # 匹配一级目录
            soup = bs(response.text, 'html.parser')
            primary_menu = soup.select('#primary-menu > div > ul > li > a')[0:-1]  # 最后一个目录url为None,剃掉
            for i in primary_menu:
                url = i.get('href')
                yield scrapy.Request(url, callback=self.parse)

        if re.match(r'https://mb.com.ph/\w+/$', response.url):
            soup = bs(response.text, 'html.parser')
            for i in soup.select('#topics-menu > div > ul > li > a'):
                url = i.get('href')
                yield scrapy.Request(url, callback=self.parse)

        if re.match(r'https://mb.com.ph/category/', response.url):  # 匹配二级目录下的文章们
            soup = bs(response.text, 'html.parser')
            for i in soup.select('h4.title > a'):
                url = i.get('href')
                yield scrapy.Request(url, callback=self.parse_item)

            for i in soup.select('h6.title > a'):
                url = i.get('href')
                yield scrapy.Request(url, callback=self.parse_item)


    def parse_item(self, response):
        item = DemoItem()
        soup = bs(response.text, 'html.parser')
        item['title'] = soup.select('div.breadcrumbs > span')[-1].text
        item['category1'] = soup.select('div.breadcrumbs > span')[0].text
        item['category2'] = soup.select('div.breadcrumbs > span')[1].text
        item['abstract'] = soup.select('section.article-content > p')[0].text

        ts = soup.select('p.published')[0].text  # 文章时间字符串例如 ts = 'Published October 22, 2020, 4:32 PM' #下面将ts 格式化
        month = Util.month2[ts.split(',')[0].split(' ')[1]]
        date = ts.split(',')[1] + '-' + month + '-' + ts.split(',')[0].split(' ')[2]

        ttt = ts.split(',')[-1].split(' ')  # ttt = ['', '4:32', 'PM']
        if ttt[-1] == 'PM':
            shi = int(ttt[-2].split(':')[0]) + 12
            time = str(shi) + ":" + ttt[-2].split(':')[1] + ":" + '00'
        else:
            shi = int(ttt[-2].split(':')[0])
            time = str(shi) + ":" + ttt[-2].split(':')[1] + ":" + '00'
        datetime = date + ' ' + time

        item['pub_time'] = datetime
        item['images'] = [i.get(' data-cfsrc') for i in soup.select('section.article-content > figure >img')]

        ss = ""  # strf  body
        for s in soup.select('section.article-content > p'):
            ss += s.text + r'\n'

        item['body'] = ss

        yield item
