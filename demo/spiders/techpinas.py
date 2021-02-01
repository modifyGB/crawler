import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class techpinasSpider(scrapy.Spider):
    name = 'techpinas'
    website_id = 492 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.techpinas.com/']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('.section .post-outer a.read-more'):
            yield Request(i.attrs['href'],callback=self.parse1)
        yield Request(html.select('.section a.blog-pager-older-link')[0].attrs['href'])

    def parse1(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text)
        item['title'] = html.select('.post-header > h1')[0].text
        item['body'] = ''
        flag = False
        for i in html.select('.post-body.entry-content > div,.post-body.entry-content i,.post-body.entry-content > h3'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = self.timeformat(html.select('abbr.published')[0].text)
        item['images']=[]
        for i in html.select('.post-body.entry-content img'):
            item['images'].append(i.attrs['src'])
        yield item

    def timeformat(self, string):
        list1 = string.split(' ')
        list2 = list1[0].split('/')
        return list2[2]+'-'+list2[0]+'-'+list2[1]+' '+list1[1]