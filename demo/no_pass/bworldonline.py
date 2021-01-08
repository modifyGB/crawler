import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class bworldonlineSpider(scrapy.Spider):
    name = 'bworldonline'
    website_id = 483 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.bworldonline.com/']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_rht',
        'password' : 'dg_rht',
        'db' : 'dg_test'
    }

    def parse(self, response):
        html = BeautifulSoup(response.text)
        if response.url == 'https://www.bworldonline.com/':
            for i in html.select('#menu-main-menu > li > a[href^="https://www.bworldonline.com/category/"]'):
                yield Request(i.attrs['href'])

        elif re.findall(r'https://www.bworldonline.com/category/\S+',response.url) != []:
            list = response.url.split('/')
            category1 = list[4]
            category2 = list[5]
            for i in html.select('.td-ss-main-content .td-module-thumb > a'):
                yield Request(i.attrs['href'],meta={'category1':category1,'category2':category2})
            for i in html.select('.td-pb-span12 .td-big-grid-wrapper .td-module-thumb > a'):
                yield Request(i.attrs['href'],meta={'category1':category1,'category2':category2})
        else:
            item = DemoItem()
            item['title'] = html.select('.entry-title')[0].text
            item['category1'] = response.meta['category1']
            item['category2'] = response.meta['category2']
            item['body'] = ''
            flag = False
            for i in html.select('.td-post-content-area .column-meta ~ p'):
                item['body'] += (i.text+'\n')
                if i.text != '' and flag == False:
                    flag = True
                    item['abstract'] = i.text
            item['pub_time'] = Util.format_time2(html.select('.td-post-date > time')[0].text)
            if html.select('.td-post-content-area .td-post-featured-image img') != []:
                item['images'] = [html.select('.td-post-content-area .td-post-featured-image img')[0].attrs['src'],]
            yield item
