import json
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
    start_urls = ['https://www.spot.ph/',]
                  # 'https://www.spot.ph/eatdrink?ref=nav-primary',]
                  # 'https://www.spot.ph/newsfeatures?ref=nav-primary',
                  # 'https://www.spot.ph/arts-culture?ref=nav-primary',
                  # 'https://www.spot.ph/entertainment?ref=channel',
                  # 'https://www.spot.ph/things-to-do?ref=nav-primary',
                  # 'https://www.spot.ph/shopping?ref=nav-primary',]
                  # 'https://www.spot.ph/top-list?ref=nav-primary']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_zjy',
        'password': 'dg_zjy',
        'db' : 'dg_test'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(SpotSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self,response):
        soup = bs(response.text,"html.parser")
        for a in soup.find("div","c-nav c-nav--sub").find_all("a"):
            if a.text.strip() == "Spot Listings" or a.text.strip() == "Spot Japan":
                pass
            else:
                url = 'https://www.spot.ph' + a.get("href")
                yield scrapy.Request(url,callback=self.parse2)

    def parse2(self, response):
        # meta = {}
        soup = bs(response.text,"html.parser")
        # category1 = soup.find(class_="section-label header4 light mb-3").text.strip()
        # meta["category1"] = category1
        # meta["category2"] = None
        # meta["pub_time"] = None
        if soup.find("div","nav nav-section"):
            url = [a.get("href") for a in soup.find("div","nav nav-section").find_all("a")]
            for u in url:
                if u:
                    yield scrapy.Request(u,callback=self.parse_news_list)
        else:
            yield scrapy.Request(response.url,callback=self.parse_news_list)


    def parse_news_list(self,response):
        soup = bs(response.text, "html.parser")
        s_url = 'https://api.summitmedia-digital.com/spot/v1/channel/get/'
        if soup.find("div","nav nav-section"):
            category2 = soup.find(class_="section-label header4 light mb-3").text.strip() if soup.find(class_="section-label header4 light mb-3") else None
            response.meta["category2"] = category2
            for i in range(0,670):
                if i==0:
                    if soup.find("div","section-header").find("h1").text == "Top 10 Lists":
                        url = s_url + response.url.split("/")[-2] + '__' + response.url.split("/")[-1] + '/0/20'
                    else:
                        url = s_url + response.url.split("/")[-1] + '/0/20'
                else:
                    if soup.find("div","section-header").find("h1").text == "Top 10 Lists":
                        url = s_url + response.url.split("/")[-2] + '__' + response.url.split("/")[-1] + "/" + str(i) + '/12'
                    else:
                        url = s_url + response.url.split("/")[-1] + "/" + str(i) + '/12'
                yield scrapy.Request(url,callback=self.parse_news_url)
        else:
            response.meta["category2"] = None
            for i in range(0,670):
                if i==0:
                    url = s_url + response.url.split("/")[-1].split("?")[0] + "/0/20"
                else:
                    url = s_url + response.url.split("/")[-1].split("?")[0] + "/" + str(i) +"/12"
                yield scrapy.Request(url,callback=self.parse_news_url)

    def parse_news_url(self,response):
        meta = {}
        soup = bs(response.text,"html.parser")
        results = json.loads(response.text)

        if soup.find("h1","break-long-words exception-message") == None  and results != []:
            for i in range(0, len(results)):
                news_url = 'https://www.spot.ph' + results[i]["url"]
                meta["title"] = results[i]["title"]
                meta["pub_time"] = Util.format_time(results[i]["date_published"])
                print(news_url)
                print('\n')
                yield scrapy.Request(news_url, callback=self.parse_news, meta=meta)
                # #测试？
                if self.time == None or int(results[i]["date_published"]) >= int(self.time):
                    # if i < len(results):
                    #     continue
                    # else:
                        yield Request(news_url,meta=response.meta,callback=self.parse_news_url)
                else:
                    self.logger.info('时间截止')
        else:
            pass



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
        images = [img.get("src") for img in soup.find("section","article-content data-artcl-cnt").find_all("img")] if soup.find("section","article-content data-artcl-cnt").find_all("img") else None
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
        # yield item



