import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class coolbuster(scrapy.Spider):
    name = 'coolbuster'
    # allowed_domains = ['https://www.coolbuster.net/']
    start_urls = ['https://www.coolbuster.net/']
    website_id = 1238  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cyl',
        'password': 'dg_cyl',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(coolbuster, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['abstract'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cat1_list = html.select("nav#nav-ceebee ul li")
        for cat1 in cat1_list:
            cat_name = cat1.select_one("span").text
            meta['category1'] = cat_name  # 获取一级目录
            detail_list_url = cat1.select_one("a")['href']  # 获取一级目录对应的url
            yield Request(detail_list_url, meta=meta, callback=self.parse_2)

    def parse_2(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        details = html.select("div.blog-posts.hfeed div.date-outer")
        if details:
            for detail in details:
                if detail.select_one("h2>a") is not None:
                    detail_url = detail.select_one("h2>a")['href']
                    response.meta['abstract'] = detail.select_one("div.post-snippet").text  # 获取摘要
                    yield Request(detail_url, meta=response.meta, callback=self.parse_3)
        # 翻页
        if html.select_one("span#blog-pager-older-link a") is not None:
            next_page_url = html.select_one("span#blog-pager-older-link a")['href']  # "https://www.coolbuster.net/search?updated-max=2020-07-28T07:58:00%2B08:00&max-results=20"
            ex = ".*?max=(.{10}).*?T(.{8}).*?"
            ddl = re.findall(ex, next_page_url)  # [('2020-07-28', '07:58:00')]
            ddl = ' '.join(ddl[0])  #2020-07-28 07:58:00
            ddl = Util.format_time3(ddl)  # 1595894280
            if (self.time == None or ddl >= int(self.time)):
                yield scrapy.Request(next_page_url, meta=response.meta, callback=self.parse_2)
            else:
                self.logger.info('时间截止')

    def parse_3(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one("div.post.hentry h1") is not None:  # 获取标题
            item['title'] = html.select_one("div.post.hentry h1").text
        item['body'] = ''  # 获取正文内容
        if html.select_one("div.post-body.entry-content") is not None:
            item['body'] += html.select_one("div.post-body.entry-content").text
        item['images'] = []  # 获取图片链接
        if html.select("div.separator a"):
            images = html.select("div.separator a")
            for i in images:
                item['images'].append(i['href'])
        item['abstract'] = response.meta['abstract']  # 获取发布时间
        if html.select_one("abbr.published.updated span") is not None:
            pub = html.select_one("abbr.published.updated span").text.strip()
            pub_time = Util.format_time2(pub)
            item['pub_time'] = pub_time
        yield item