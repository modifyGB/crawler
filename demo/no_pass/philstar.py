import json
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#将爬虫类名和name字段改成对应的网站名
class philstarSpider(scrapy.Spider):
    name = 'philstar'
    website_id = 187 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.philstar.com/']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_zdx',
        'password' : 'dg_zdx',
        'db' : 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(philstarSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta["category1"] = ''
        meta["category2"] = ''
        meta["abstract"] = ''
        soup = BeautifulSoup(response.text, "html.parser")
        temp_list = soup.select_one("div#div-navig").find_all("a")
        for temp in temp_list[0:6]:
            url = temp.get("href")
            meta["category1"] = temp.text.strip()
            yield scrapy.Request(url, meta=meta, callback=self.parse_category2)

    def parse_category2(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        temp_list = soup.select_one("ul#main-navig").find_all("a")
        for temp in temp_list[1:]:
            url = temp.get("href")
            response.meta["category2"] = temp.text.strip()
            yield scrapy.Request(url, meta=response.meta, callback=self.parse_news_list)

    def parse_news_list(self,response):
        url_list = []
        soup = BeautifulSoup(response.text, "html.parser")
        if soup.find_all("div", class_="tiles late"):
            temp_list = soup.find_all("div", class_="tiles late")
            for temp in temp_list:
                response.meta["abstract"] = temp.select_one("div.news_summary a").text.strip() if temp.select_one("div.news_summary a") else None
                url = temp.select_one("div.news_title a").get("href")
                url_list.append(url)
                yield scrapy.Request(url, callback=self.parse_news)
        elif soup.select("div.microsite_article"):
            temp_list = soup.select("div.microsite_article")
            for temp in temp_list:
                response.meta["abstract"] = temp.select_one("div.microsite_article_summary").text if temp.select_one("div.microsite_article_summary")else None
                url = temp.select_one("div.microsite_article_title a").get("href") if temp.select_one("div.microsite_article_title a") else None
                url_list.append(url)
                yield scrapy.Request(url, callback=self.parse_news)
        time_list = re.findall(r"/\d+/\d+/\d+/\d+/", url_list[-1])[0].split("/")  # 每页最后一条新闻的日期
        time = time_list[1] + "-" + time_list[2] + "-" + time_list[3] + " 23:59:59"
        next_page = soup.select_one("div.next").find("a").get("href").split("µ")
        next_page = "&micro".join(next_page)
        if self.time == None or Util.format_time3(time) >= int(self.time):
            yield scrapy.Request(next_page, meta=response.meta, callback=self.parse_news_list)
        else:
            self.logger.info('时间截止')

    def parse_news(self, response):
        item = DemoItem()
        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        item["abstract"] = response.meta["abstract"]
        soup = BeautifulSoup(response.text, "html.parser")
        temp = soup.find("script", {"type": "application/ld+json"}).text
        temp = json.loads(temp)
        item["title"] = temp["headline"]
        item["images"] = temp["image"]
        pub_time_list = re.split("T|\+", temp["datePublished"])
        item["pub_time"] = pub_time_list[0] + " " + pub_time_list[1]

        body = []
        if soup.select_one("div#sports_article_writeup"):
            temp_list = soup.select_one("div#sports_article_writeup")
            temp_list = temp_list.find_all("p")
            for temp in temp_list:
                temp = temp.text.strip()
                body.append(temp)
            body = "\n".join(body).split("\xa0")
            item["body"] = " ".join(body)
        yield item