import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re

header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}

class technobaboy(scrapy.Spider):
    name = 'technobaboy'
    # allowed_domains = ['https://www.technobaboy.com/']
    start_urls = ['https://www.technobaboy.com/']
    website_id = 1246  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
            'host': '127.0.0.1',
            'user': 'root',
            'password': 'asdfghjkl',
            'db': 'dg_test'
        }

    def __init__(self, time=None, *args, **kwargs):
        super(technobaboy, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        html = BeautifulSoup(response.body.decode("utf-8"), "html.parser")
        meta = {}
        meta['category2'] = ''
        meta['abstract'] = ''
        urls = html.select("ul#menu-top-menu li a")
        for u in urls:
            topic = u.text
            meta['category1'] = topic  # 获取一级目录
            url = u['href']
            yield Request(url, headers=header, meta=meta, callback=self.parse_2)

    def parse_2(self, response):
        html = BeautifulSoup(response.text)
        detail_list = html.select("div.posts-wrap div.col-12")
        for detail in detail_list:
            abstract = detail.select_one("div.post-content.post-excerpt.cf p")
            if abstract is not None:
                response.meta['abstract'] = abstract.text  # 获取摘要
            if detail.select_one("div.post-meta.post-meta-c.post-meta-left.has-below h2 a")['href'] is not None:
                detail_url = detail.select_one("div.post-meta.post-meta-c.post-meta-left.has-below h2 a")['href']
                yield Request(detail_url, headers=header, meta=response.meta, callback=self.parse_3)
        #  翻页
        if html.select_one("time.post-date") is not None:
            ddl = html.select_one("time.post-date")['datetime']  # datetime="2021-01-30T23:00:00+08:00"
            ddl = re.split('T|\+', ddl)  # ['2021-01-30', '23:00:00', '08:00']
            ddl = ddl[0] + ' ' + ddl[1]  # 2021-01-30 23:00:00
            ddl = Util.format_time3(ddl)  # 1612018800
        else:
            ddl = None

        next_page_url_tag = html.select("span.page-numbers.label-next a")
        if next_page_url_tag:
            next_page_url = next_page_url_tag[0]['href']
            if (self.time == None or ddl >= int(self.time)):
                yield Request(next_page_url, headers=header, meta=response.meta, callback=self.parse_2)
            else:
                self.logger.info('时间截止')

    def parse_3(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one('div.post-top.cf h1.post-title') is not None:  # 获取标题
            item['title'] = html.select_one('div.post-top.cf h1.post-title').text
        item['abstract'] = response.meta['abstract']
        item['body'] = ''  # 获取正文内容
        if html.select("div.post-content.description.cf.entry-content.content-spacious p"):
            body_list = html.select("div.post-content.description.cf.entry-content.content-spacious p")
            for b in body_list:
                item['body'] += b.text.strip()
                item['body'] += "\n"
        item['images'] = []  # 获取图片链接
        image_one = html.select_one("div.featured a")
        if image_one is not None:  # 先获取单独的图片链接
            item['images'].append(image_one['href'])
        images = html.select("div.wp-block-image img")  # 获取在类似位置的图片的链接
        if images:
            for i in images:
                item['images'].append(i['src'])
        if html.select_one("time.post-date") is not None:
            pub_time = html.select_one("time.post-date").text.strip()
            pub_time = Util.format_time2(pub_time)
            item['pub_time'] = pub_time
        yield item

