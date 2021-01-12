import json

import requests
import scrapy
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
from demo.util import Util
from demo.items import DemoItem
import re
import time


class SpotSpider(scrapy.Spider):
    name = 'spot'
    allowed_domains = ['www.spot.ph','api.summitmedia-digital.com']
    website_id = 495  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    start_urls = [#'https://www.spot.ph/',]
                  'https://www.spot.ph/eatdrink?ref=nav-primary',
                  'https://www.spot.ph/newsfeatures?ref=nav-primary',
                  'https://www.spot.ph/arts-culture?ref=nav-primary',
                  'https://www.spot.ph/entertainment?ref=channel',
                  'https://www.spot.ph/things-to-do?ref=nav-primary',
                  'https://www.spot.ph/shopping?ref=nav-primary',
                  'https://www.spot.ph/top-list?ref=nav-primary']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_rht',
        'password': 'dg_rht',
        'db' : 'dg_test'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(SpotSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self,response):
        soup = bs(response.text,"html.parser")
        if soup.find("div","nav nav-section"):
            for a in soup.find("div","nav nav-section").find_all("a"):
                url = a.get("href")
                yield scrapy.Request(url,callback=self.parse_list)
        else:
            yield scrapy.Request(response.url,callback=self.parse_list)

    def parse_list(self,response):
        meta = {}
        soup = bs(response.text, "html.parser")
        s_url = 'https://api.summitmedia-digital.com/spot/v1/channel/get/'
        if soup.find("div","nav nav-section"):
            p=0
            while p>=0:
                if soup.find("div","section-header").find("h1").text == "Top 10 Lists":
                    url = s_url + response.url.split("/")[-2] + '__' + response.url.split("/")[-1] + '/' + str(p) +'/20'
                else:
                    url = s_url + response.url.split("/")[-1] + '/' + str(p) +'/20'
                # self.logger.info(url)
                results = json.loads(requests.get(url).text)
                if requests.get(url).status_code == 200 and results != []:
                    p = p + 1
                    pub_time1 = results[-1]["date_published"]
                    if self.time == None or int(pub_time1) >= int(self.time):
                        for i in range(0, len(results)):
                            news_url = 'https://www.spot.ph' + results[i]["url"]
                            meta["title"] = results[i]["title"]
                            meta["pub_time"] = Util.format_time(results[i]["date_published"])
                            # self.logger.info(news_url)
                            # self.logger.info('\n')
                            yield Request(news_url, callback=self.parse_news, meta=meta)
                    else:
                        self.logger.info('时间截止')
                        p = -1
                else:
                    p = -1
        else:
            p=0
            while p>=0:
                url = s_url + response.url.split("/")[-1].split("?")[0] + '/' + str(p) +'/20'
                results = json.loads(requests.get(url).text)
                if requests.get(url).status_code == 200 and results != []:
                    p = p + 1
                    pub_time1 = results[-1]["date_published"]
                    if self.time == None or int(pub_time1) >= int(self.time):
                        for i in range(0, len(results)):
                            news_url = 'https://www.spot.ph' + results[i]["url"]
                            meta["title"] = results[i]["title"]
                            meta["pub_time"] = Util.format_time(results[i]["date_published"])
                            # self.logger.info(news_url)
                            # self.logger.info('\n')
                            yield Request(news_url, callback=self.parse_news, meta=meta)
                    else:
                        self.logger.info('时间截止')
                        p = -1
                else:
                    p = -1

    def parse_news(self, response):
        item = DemoItem()
        soup = bs(response.text,"html.parser")
        category1 = soup.find("div","breadcrumbs header5").find("a").text.strip() if soup.find("div","breadcrumbs header5") else None
        item["category1"] = category1
        category2 = soup.find("div","breadcrumbs header5").find_all("a")[-1].text.strip() if soup.find("div","breadcrumbs header5") else None
        if category2 == category1:
            category2 = None
        item["category2"] = category2
        item["pub_time"] = response.meta["pub_time"]
        # title = soup.find("h1","gtm-articleContent title mb-2 header1").text.strip() if soup.find("h1","gtm-articleContent title mb-2 header1") else None
        # item["title"] = title
        item["title"] = response.meta["title"]
        images = [img.get("src") for img in soup.find("section","article-content data-artcl-cnt").find_all("img")] if soup.find("section","article-content data-artcl-cnt") else None
        item["images"] = images
        if soup.find("p", "blurb mb-2 header6"):
            abstract = soup.find("p","blurb mb-2 header6").text.strip()
        else:
             abstract = soup.find("section","article-content data-artcl-cnt").find("p").text.strip() if soup.find("section","article-content data-artcl-cnt") else None
        item["abstract"] = abstract
        body = ''
        if soup.find("section", "article-content data-artcl-cnt"):
            for p in soup.find("section", "article-content data-artcl-cnt").find_all("p"):
                body += p.text.strip()+'\n'
        else:
            body = None
        item["body"] = body
        self.logger.info(item)
        self.logger.info('\n')
        yield item



