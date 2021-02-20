import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class yehey(scrapy.Spider):
    name = 'yehey'
    # allowed_domains = ['https://yehey.com/']
    start_urls = ['https://yehey.com/']
    website_id = 1225  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cyl',
        'password': 'dg_cyl',
        'db': 'dg_test_source'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(yehey, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cat1 = html.select_one("li#menu-item-5581 a").text
        meta['category1'] = cat1  # 获取一级目录
        cat1_url = html.select_one("li#menu-item-5581 a")['href']
        yield scrapy.Request(cat1_url, meta=meta, callback=self.parse_category2)

    def parse_category2(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        cat2s = html.select("li#menu-item-5581>ul.sub-menu>li")
        for c in cat2s:
            cat2_url = c.select_one("a")['href']
            cat2 = c.select_one("a").text
            response.meta['category2'] = cat2  # 获取二级目录
            yield scrapy.Request(cat2_url, meta=response.meta, callback=self.parse_category3)

    def parse_category3(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        detail_list = html.select("main#main>article")
        for d in detail_list:
            detail_url = d.select_one("h2.entry-title.th-text-md.th-mb-0 a")['href']  # 获取静态加载的url
            yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_detail)  # 处理静态的数据

        page_text = response.text
        ex = '<script type="text/javascript">.*?currentday%22%3A%22(.*?)%22%2C%22'
        if re.findall(ex, page_text, re.S):  # currentday: "24.10.20"
            request_url = "https://yehey.com/?infinity=scrolling"
            page_text = response.text
            # 每一个数据包的data里面的currentday的值是上一个加载出来的数据包通过ajax请求拿到的数据中的currentday的值
            ex1 = '<script type="text/javascript">.*?currentday%22%3A%22(.*?)%22%2C%22'
            currentday = re.findall(ex1, page_text, re.S)[0]  # 24.10.20
            ex2 = '.*?category/(.*?)/'
            category_name = re.findall(ex2, response.url, re.S)[0]  # business
            data = {
                'page': '2',
                'currentday': currentday,
                'query_args[category_name]': category_name
            }
            # if (requests.post(request_url, data).json()['postflair']):
            if 'postflair' in requests.post(request_url, data).json().keys():
                dic_url = requests.post(request_url, data).json()['postflair']  # 拿到动态加载出来的详情页的url
                for news_url in dic_url.keys():
                    yield scrapy.Request(news_url, meta=response.meta, callback=self.parse_detail)

                page = 3
                while 1:
                    if 'currentday' in requests.post(request_url, data).json().keys():
                        dynamic_currentday = requests.post(request_url, data).json()['currentday']  # 每一个数据包的data里面的currentday的值是上一个加载出来的数据包通过ajax请求拿到的数据中的currentday的值
                        data = {
                            'page': str(page),
                            'currentday': dynamic_currentday,
                            'query_args[category_name]': category_name
                            }
                        page = page + 1
                        time.sleep(1)
                        if 'postflair' in requests.post(request_url, data).json().keys():
                            dic_url = requests.post(request_url, data).json()['postflair']
                            for news_url in dic_url.keys():  # 进行是否继续对动态数据包发起请求的判断
                                if self.time == None or Util.format_time3(time) >= int(self.time):
                                    yield scrapy.Request(news_url, meta=response.meta, callback=self.parse_detail)
                                else:
                                    self.logger.info('时间截止')
                    else:
                        break


    def parse_detail(self,response):
        item = DemoItem()
        html = BeautifulSoup(response.text, 'html.parser')
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.find('h1', class_='entry-title th-mb-0 sm:th-text-8xl th-text-4xl').text.strip():  # 获取标题
            item['title'] = html.find('h1', class_='entry-title th-mb-0 sm:th-text-8xl th-text-4xl').text.strip()
        item['body'] = ''  # 获取正文内容
        if html.select("div.entry-content.th-content p"):
            bodies = html.select("div.entry-content.th-content p")
            item['abstract'] = bodies[0].text  # 获取摘要
            for b in bodies:
                item['body'] += b.text.strip()
                item['body'] += "\n"
        item['images'] = []  # 获取图片链接
        if html.select_one("header#primary-header img") is not None:  # 获取单独在标题的图片
            image_one = html.select_one("header#primary-header img")['src']
            item['images'].append(image_one)
        if html.select("div.entry-content.th-content a>img"):  # 获取在段落中的图片
            imgaes = html.select("div.entry-content.th-content a>img")
            for i in imgaes:
                item['images'].append(i['src'])
        if html.select_one("time.entry-date.published") is not None:  # 获取发布时间
            pub = html.select_one("time.entry-date.published")['datetime']
            pub_time = re.split('T|\+', pub)  # datetime="2021-01-30T23:00:00+08:00"
            pubtime = pub_time[0] + ' ' + pub_time[1]  # ['2021-01-30', '23:00:00', '08:00']
            item['pub_time'] = pubtime  # 2021-01-30 23:00:00
        yield item