
# 此文件包含的头文件不要修改
import datetime

import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import FormRequest, Request
import re
import json
import time

#将爬虫类名和name字段改成对应的网站名
class lusaSpider(scrapy.Spider):
    name = 'lusa'
    website_id = 683  # 网站的id(必填)
    language_id = 2122  # 所用语言的id
    start_urls = ['https://www.lusa.pt']
    sql = {  # sql配置
            'host': '127.0.0.1',#新的
            'user': 'root',
            'password': 'asdfghjkl',
            'db': 'dg_test'
        }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(lusaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):

        soup = BeautifulSoup(response.text, features="lxml")
        category1_hrefList = []
        category1_nameList = []
        categories = soup.find("nav", class_="navbar navbar-default").select("li")[1:8] if soup.find("nav", class_="navbar navbar-default") else None
        for category in categories:
            category1_hrefList.append(category.find("a").get("href"))
            category1_nameList.append(category.text)
        for category in category1_hrefList:
            yield scrapy.Request(category, callback=self.parse_category1,meta={'page':1})

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        response.meta['page'] += 1
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": "",
            "__VIEWSTATEGENERATOR": "7AADE825",
            "hdPageNumber": response.meta['page'],
            "hdTotalRecords": ""
        }

        data["hdPageNumber"] += 1
        data['__VIEWSTATE'] = re.findall(r'<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="(\S+?)"',response.text)[0]
        data['hdTotalRecords'] = re.findall(r'<input type="hidden" name="hdTotalRecords" id="hdTotalRecords" value="(\d+)"', response.text)[0]
        self.logger.info(re.findall(r'<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="(\S+?)"',response.text)[0])
        self.logger.info(data["hdPageNumber"])
        if self.time == None or Util.format_time3(time_adjustment(soup.select_one('div.col-sm-12 ul li').text + ":00")) >= int(self.time):
            yield Request(response.url, body=json.dumps(data), method='POST', meta=response.meta,callback=self.parse_category1)
        else:
            self.logger.info('时间截止')
        temp_soup = BeautifulSoup(response.text, features="lxml")
        item = DemoItem()
        item["category1"] = temp_soup.find("h2", class_="heading-md h-red").text if temp_soup.find("h2", class_="heading-md h-red") else None
        news_hrefList = []
        news_hrefs = temp_soup.find("div", id="MIDDLE") if temp_soup.find("div", id="MIDDLE") else None
        h3_list = news_hrefs.find_all("h3")
        for h3 in h3_list:
            news_url = h3.find("a").get("href")
            news_hrefList.append(news_url)
        for url in news_hrefList:
            yield scrapy.Request(url, callback=self.parse_detail, meta={"item": item})


    def parse_detail(self, response):
        item = DemoItem()
        item["category1"] = response.meta["item"]["category1"]
        soup = BeautifulSoup(response.text, features="lxml")
        item["title"] = soup.find("h2").text if soup.find("h2") else None
        item["abstract"] = soup.find("div", class_="lt-text").find("p").text if soup.find("div", class_="lt-text").find("p") else None
        imgs = []
        img = soup.find("div", class_="article col-md-12 m-bottom20").find_all("img") if soup.find("div", class_="article col-md-12 m-bottom20") else None
        for i in img:
            imgs.append(i.get("src"))
        item["images"] = imgs
        p_list = soup.find("div", class_="lt-text").find_all("p") if soup.find("div", class_="lt-text") else None
        body = ""
        for p in p_list:
            body += p.text.strip() + "\n"
        item["body"] = body
        pub_time = soup.find("ul", class_="list-inline item-info bordone").find("li").text if soup.find("ul", class_="list-inline item-info bordone") else None
        pub_time_adjusted = datetime.datetime.strptime(pub_time, '%d-%m-%Y %H:%M').strftime("%Y-%m-%d %H:%M")
        item["pub_time"] = pub_time_adjusted

        yield item


def time_adjustment(input_time):
    time_list = re.split(" |:|-", input_time)
    year = time_list[2]
    month = time_list[1]
    day = time_list[0]
    hour = time_list[3]
    minute = time_list[4]
    second = time_list[5]
    return "%s-%s-%s %s:%s:%s" % (year, month, day, hour, minute, second)