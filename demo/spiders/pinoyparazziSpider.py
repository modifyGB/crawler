import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class pinoyparazzi(scrapy.Spider):
    name = 'pinoyparazzi'
    # allowed_domains = ['https://www.pinoyparazzi.com/']
    start_urls = ['https://www.pinoyparazzi.com/']
    website_id = 1241  # 网站的id(必填)
    language_id = 1880  # 所用语言的id
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cyl',
        'password': 'dg_cyl',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(pinoyparazzi, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cat1s = html.select("ul#menu-header-1>li>a")
        for c in cat1s:
            cat1 = c.text
            meta['category1'] = cat1
            detail_list_url = c['href']
            yield scrapy.Request(detail_list_url, meta=meta, callback=self.parse_category2)

    def parse_category2(self, response):
        html = BeautifulSoup(response.text)
        details = html.select("div.td-block-row div.td-block-span6")
        for d in details:
            detail_url = d.select_one("h3 a")["href"]
            yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_category3)

        if html.select("time.entry-date.updated.td-module-date"):
            ddl = html.select("time.entry-date.updated.td-module-date")[-1]['datetime']
            ddl = re.split('T|\+', ddl)  # ['2021-01-30', '23:00:00', '08:00']
            ddl = ddl[0] + ' ' + ddl[1]  # 2021-01-30 23:00:00
            ddl = Util.format_time3(ddl)  # 1612018800
        else:
            ddl = None

        pages = html.select("div.page-nav.td-pb-padding-side a")
        if pages:
            page = pages[-1]
            if page.select_one("i") is not None:
                next_page_url = page['href']
                if (self.time == None or ddl >= int(self.time)):
                    yield scrapy.Request(next_page_url, meta=response.meta, callback=self.parse_category2)
                else:
                    self.logger.info('时间截止')

    def parse_category3(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one("h1.entry-title") is not None:
            item['title'] = html.select_one("h1.entry-title").text
        item['body'] = ''
        bodies = html.select("div.td-post-content.tagdiv-type p")
        if bodies:
            for b in bodies:
                item['body'] += b.text
                item['body'] += '\n'
            # item['abstract'] = bodies[0].text
            for b in bodies:
                if b.text is not '':
                    item['abstract'] = b.text
                    break
        item['images'] = []
        images = html.select("div.td-post-content.tagdiv-type figure")
        if images:
            for i in images:
                item['images'].append(i.select_one("img")['src'])
        if html.select_one("time.entry-date.updated.td-module-date") is not None:
            pub1 = html.select_one("time.entry-date.updated.td-module-date")['datetime']
            pub = re.split('T|\+', pub1)
            pub_time = pub[0] + ' ' + pub[1]
            item['pub_time'] = pub_time
        yield item