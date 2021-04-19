# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
from datetime import datetime
import time


def sanmarg_time_switch1(time_string):
    # 23 December 2020,17:10 IST
    return datetime.strptime(time_string, "%d %B %Y,%H:%M IST")


def sanmarg_time_switch2(time_string):
    # 23 December 2020,17:10 IST
    # 返回时间戳
    return Util.format_time3(str(datetime.strptime(time_string, "%d %B %Y,%H:%M IST")))


# 将爬虫类名和name字段改成对应的网站名
class SanmargSpider(scrapy.Spider):
    name = 'sanmarg_spider'
    website_id = 1017  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://sanmarg.in/']
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cbs',
        'password': 'dg_cbs',
        'db': 'dg_test_source'
    }
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/89.0.4389.114 Safari/537.36 '
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(SanmargSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], headers=self.headers, callback=self.parse)

    def parse(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        for a in soup.select(".footer-block-wrapper.clearfix div.menu-footer-categories-container li a"):
            yield scrapy.Request(a.get("href"), callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        firstnews = soup.select_one("#content #primary section .first-block-wrapper .toppost-wrapper.clearfix "
                                    ".post-title a").get("href")
        yield scrapy.Request(firstnews, callback=self.parse_detail)
        yield scrapy.Request(firstnews, callback=self.parse_first_news)

    def parse_detail(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        item = DemoItem()
        item['title'] = soup.select_one("div#content #primary article header h1").text.strip()
        item['pub_time'] = sanmarg_time_switch1(
            re.split("Updated:|, ", soup.select_one("div#content #primary article header div").text.strip())[-1])
        item['images'] = [
            soup.select_one("div#content #primary article .entry-content .post_image img").get("data-src")]
        item['abstract'] = soup.select_one(
            "div#content #primary article .entry-content .post-content .has-content-area p").text.strip()
        item['body'] = ''.join(p.text.strip() + '\n' for p in soup.select(
            "div#content #primary article .entry-content .post-content .has-content-area p"))
        splited_url = response.url.split("https://sanmarg.in/")[1]
        item['category1'] = splited_url.split("/", 1)[0]
        item['category2'] = None if splited_url.split("/", 2)[2] == '' else splited_url.split("/", 2)[1]
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        yield item

    def parse_first_news(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        previous_url = soup.select_one("div#content #primary nav .nav-links a").get("href") if soup.select_one("div#content #primary nav .nav-links a") else None
        next_url = soup.select_one("div#content #primary nav .nav-links .nav-next a").get("href") if soup.select_one("div#content #primary nav .nav-links .nav-next a") else None
        yield scrapy.Request(previous_url, callback=self.parse_backward) if previous_url else None  # 向后parse
        yield scrapy.Request(next_url, callback=self.parse_forward) if next_url else None # 向前parse

    def parse_forward(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        yield scrapy.Request(response.url, callback=self.parse_detail)
        next_url = soup.select_one("div#content #primary nav .nav-links .nav-next a").get("href") if soup.select_one("div#content #primary nav .nav-links .nav-next a") else None
        yield scrapy.Request(next_url, callback=self.parse_forward) if next_url else None

    def parse_backward(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        yield scrapy.Request(response.url, callback=self.parse_detail)
        previous_url = soup.select_one("div#content #primary nav .nav-links a").get("href") if soup.select_one("div#content #primary nav .nav-links a") else None
        TimeStamp = sanmarg_time_switch2(
            re.split("Updated:|, ", soup.select_one("div#content #primary article header div").text.strip())[-1])
        if previous_url is None:
            self.logger("前面无新闻")
        elif self.time is None or TimeStamp >= self.time:
            yield scrapy.Request(previous_url, callback=self.parse_backward)
        else:
            self.logger.info("时间截止")
