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



class pinoytechblog(scrapy.Spider):
    name = 'pinoytechblog'
    # allowed_domains = ['example.com']
    start_urls = ['https://www.pinoytechblog.com/']
    website_id = 1245  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cyl',
        'password': 'dg_cyl',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(pinoytechblog, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['abstract'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cats = html.select("ul#menu-main-1 li a")
        for c in cats:
            cat_url = c.attrs['href']
            meta['category1'] = c.text  # 获取一级目录
            yield Request(cat_url, headers=header, meta=meta, callback=self.parse_2)



    def parse_2(self, response):
        html = BeautifulSoup(response.text)
        item_list = html.select("div.theiaStickySidebar li.list-post")
        for i in item_list:
            response.meta['abstract'] = i.select_one('div.item-content.entry-content p').text
            detail_url = i.select_one('h2 a').attrs['href']  # 获取详情页的url
            yield Request(detail_url, headers=header, meta=response.meta, callback=self.parse_3)

        # 翻页
        ddl = html.select_one("time.entry-date.published").text.strip()
        ddl = Util.format_time2(ddl)
        ddl = Util.format_time3(ddl)

        pages = html.select('div#main ul.page-numbers li')
        page = pages[-1]
        if page.select('a'):
            url = page.select_one('a').attrs['href']
            if(self.time==None or ddl>=int(self.time)):
                yield Request(url, headers=header, meta=response.meta, callback=self.parse_2)
            else:
                self.logger.info('时间截止')


    def parse_3(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one('div#main div.header-standard.header-classic.single-header h1') is not None:  # 获取标题
            item['title'] = html.select_one('div#main div.header-standard.header-classic.single-header h1').text
        item['body'] = ''  # 获取正文内容
        if html.find('div',class_='inner-post-entry entry-content').select('p') is not None:
            body_list = html.find('div',class_='inner-post-entry entry-content').select('p')
            if body_list:
                for body in body_list:
                    item['body'] += body.text.strip()
                    item['body'] += '\n'
        item['images'] = []  # 获取图片链接
        for i in html.select("div#main div.post-entry.blockquote-style-2 div.inner-post-entry.entry-content p"):
            if i.select_one('img') is not None:
                item['images'].append(i.select_one('img').attrs['src'])
        item['abstract'] = response.meta['abstract']
        if html.select_one("time.entry-date.published") is not None:  # 获取发布时间
            pub_time = html.select_one("time.entry-date.published").text.strip()
            pub_time = Util.format_time2(pub_time)
            item['pub_time'] = pub_time
        yield item












