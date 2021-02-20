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


class mattscradle(scrapy.Spider):
    name = 'mattscradle'
    #allowed_domains = ['example.com']
    start_urls = ['https://mattscradle.com/']
    website_id = 1232  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cyl',
        'password': 'dg_cyl',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(mattscradle, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.body.decode("utf-8"), "html.parser")
        urls = html.select("ul#menu-home li")
        for u in urls:
            meta = {}
            meta['category2'] = ''
            if u.select_one('a').attrs['href'] in ['https://mattscradle.com/about/','https://mattscradle.com/privacy-policy/']:  # 排除非新闻网页的链接
                continue
            url = u.select_one('a').attrs['href']
            topic = u.select_one('a').text
            meta['category1'] = topic  # 获取一级目录
            yield Request(url, headers=header, meta=meta, callback=self.parse_2)


    def parse_2(self, response):
        html = BeautifulSoup(response.text)
        news_list = html.select("div.content div")
        for n in news_list:
            if n.select_one("div.headline_area h2 a") is not None:
                description = n.select_one("div.post_content.post_excerpt p")
                if description is not None:
                    detail_url = description.select_one("a").attrs['href']
                    response.meta['abstract'] =description.text  # 获取摘要
                    yield Request(detail_url, headers=header, meta=response.meta, callback=self.parse_3)

        # 翻页
        next_page = html.select_one("div.prev_next span.previous_posts")
        if next_page.select_one("a") is not None:
            next_page_url = next_page.select_one("a").attrs['href']
            yield Request(next_page_url, headers=header, meta=response.meta, callback=self.parse_2)



    def parse_3(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one('div.headline_area h1') is not None:  # 获取标题
            item['title'] = html.select_one('div.headline_area h1').text
        item['body'] = ''  # 获取正文内容
        if html.find('div', class_='post_content').select('p') is not None:
            body_list = html.find('div', class_='post_content').select('p')
            if (body_list):
                for body in body_list:
                    item['body'] += body.text.strip()
                    item['body'] += '\n'
        item['images'] = []  # 获取图片链接
        if html.select('div.post_content p'):
            all_body = html.select('div.post_content p')
            for a in all_body:
                if a.select_one('img') is not None:
                    item['images'].append(a.select_one('img').attrs['src'])
        item['abstract'] = response.meta['abstract']
        if html.select_one('span.post_date.date_modified') is not None:  # 获取发布时间
            pub_time = html.select_one('span.post_date.date_modified').text.strip()
            pub_time = Util.format_time2(pub_time)
            item['pub_time'] = pub_time
        yield item






