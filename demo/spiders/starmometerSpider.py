import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}

class starmometer(scrapy.Spider):
    name = 'starmometer'
    # allowed_domains = ['https://starmometer.com/']
    start_urls = ['https://starmometer.com/']
    website_id = 1239  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cyl',
        'password': 'dg_cyl',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(starmometer, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['abstract'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cats = html.select("ul#menu-main-menu-1 li a")
        for cat in cats:
            meta['category1'] = cat.text  # 获取一级目录
            detail_list_url = cat.attrs['href']  # 获取一级目录对应的url
            yield scrapy.Request(detail_list_url, headers=header, meta=meta, callback=self.parse_2)

    def parse_2(self, response):
        html = BeautifulSoup(response.text)
        detail_lists = html.select("section#mh-loop article")
        for d in detail_lists:
            detial_url = d.select_one("h3 a").attrs['href']
            response.meta['abstract'] = d.select_one("div.mh-excerpt").text  # 获取摘要
            yield Request(detial_url, headers=header, meta=response.meta, callback=self.parse_3)

        if html.select('.loop-data>.meta'):
            ddl = html.select('.loop-data>.meta')[0].text.strip()  # February 3, 2021 // 0 Comments
            ex = '(.*?)//.*?'
            ddl = re.findall(ex, ddl, re.S)  # ['February 3, 2021 ']
            ddl = Util.format_time2(ddl[0])  # 2021-02-03 00:00:00
            ddl = Util.format_time3(ddl)  # 1612281600
        else:
            ddl = None
        # 翻页
        next_page = html.select_one("div.loop-pagination.clearfix a.next.page-numbers")
        if next_page is not None:
            next_page_url = next_page.attrs['href']
            if (self.time == None or ddl >= int(self.time)):
                yield Request(next_page_url, headers=header, meta=response.meta, callback=self.parse_2)
            else:
                self.logger.info('时间截止')



    def parse_3(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one("header.post-header h1.entry-title") is not None:  # 获取标题
            item['title'] = html.select_one("header.post-header h1.entry-title").text
        item['body'] = ''
        item['images'] = []  # 获取图片链接
        if html.select("div.entry.clearfix p"):
            bodys = html.select("div.entry.clearfix p")  # 获取正文内容
            for b in bodys:
                item['body'] += b.text.strip()
                item['body'] += "\n"
                if b.select_one("img") is not None:
                    item['images'].append(b.select_one("img").attrs['src'])
        if html.select_one("header.post-header p span") is not None:  # 获取发布时间
            pub_time = html.select_one("header.post-header p span").text
            pub_time = Util.format_time2(pub_time)
            item['pub_time'] = pub_time
        item['abstract'] = response.meta['abstract']
        yield item