import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class chinaEmbassy(scrapy.Spider):
    name = 'china-embassy'
    #allowed_domains = ['http://ph.china-embassy.org/eng/']
    start_urls = ['http://ph.china-embassy.org/eng/']
    website_id = 1235  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cyl',
        'password': 'dg_cyl',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(chinaEmbassy, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['url'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cat1s = html.select("div.menu.fl ul li")
        for c in cat1s:
            if c.text not in ['Home']:
                meta['category1'] = c.text
                detail_list_url = "http://ph.china-embassy.org/eng/" + c.select_one("a")['href']
                yield scrapy.Request(detail_list_url, meta=meta, callback=self.parse_category2)

    def parse_category2(self, response):
        html = BeautifulSoup(response.text)
        detail = html.select("div.nbox_ul>ul")
        next_detail = detail[1]
        if next_detail.select("li"):
            response.meta['url'] = response.url
            next_detail_list = next_detail.select("li")
            for n in next_detail_list:
                detail_url = response.url + n.select_one("a")['href']
                yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_category4)

        cat2_details = detail[0]
        if cat2_details.select("li"):
            cat2_detail_list = cat2_details.select("li")
            for c in cat2_detail_list:
                cat2_detail = response.url + c.select_one("a")['href']
                cat2 = c.text
                response.meta['category2'] = cat2
                yield scrapy.Request(cat2_detail, meta=response.meta, callback=self.parse_category3)

    def parse_category3(self, response):
        html = BeautifulSoup(response.text)
        uls = html.select("div.nbox_ul ul")
        details = uls[1]
        if details.select("li"):
            response.meta['url'] = response.url
            detail = details.select("li")
            for d in detail:
                detail_url = response.url + d.select_one("a")['href']
                yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_category4)

        if html.select('div.nbox_ul ul li a'):
            ddl = html.select('div.nbox_ul ul li a')[-1].text
            ddl = re.findall(r'\((.*?)\)', ddl)
            if ddl:
                ddl = ddl[0] + ' ' + '00:00:00'
                ddl = Util.format_time3(ddl)
            else:
                ddl = None
        else:
            ddl = None
        for page in (1, 2):
            next_page_url = response.url + "default_%s.htm" % page
            if (self.time == None or ddl >= int(self.time)):
                yield scrapy.Request(next_page_url, meta=response.meta, callback=self.parse_category4)
            else:
                self.logger.info('时间截止')

    def parse_category4(self, response):
        try:
            html = BeautifulSoup(response.text, "html.parser")
            item = DemoItem()
            item['category1'] = response.meta['category1']
            item['category2'] = response.meta['category2']
            if html.select_one("div#News_Body_Title") is not None:
                item['title'] = html.select_one("div#News_Body_Title").text
            item['body'] = ''
            bodies = html.select("div#News_Body_Txt_A p")
            if bodies:
                for b in bodies:
                    item['body'] += b.text.strip()
                    item['body'] += '\n'
                for b in bodies:
                    if b.text.strip() is not '':
                        item['abstract'] = b.text.strip()
                        break
            item['images'] = []
            images = html.select("div#News_Body_Txt_A span")
            if images:
                for i in images:
                    if i.select_one("img") is not None:
                        item['images'].append(response.meta['url'] + i.select_one("img")['src'])
            pub = html.select_one("div#News_Body_Time")
            if pub is not None:
                pub1 = re.findall(r'(\d{4})/(\d{2})/(\d{2})', pub.text)
                if pub1:
                    pub_time = '-'.join(pub1[0]) + ' ' + '00:00:00'
                    item['pub_time'] = pub_time
            yield item
        except AttributeError:
            pass
