import datetime
import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import requests
import time

class HatawtabloidSpider(scrapy.Spider):
    name = 'hatawtabloid'
    website_id = 532  # 网站的id(必填)
    language_id = 2117  # 所用语言的id
    allowed_domains = ['hatawtabloid.com']
    start_urls = ['https://www.hatawtabloid.com/category/news',
                  'https://www.hatawtabloid.com/category/opinion',
                  'https://www.hatawtabloid.com/category/bulabugin',
                  'https://www.hatawtabloid.com/category/showbiz',
                  'https://www.hatawtabloid.com/category/sports',
                  'https://www.hatawtabloid.com/category/hataw-lifestyle',
                  'https://www.hatawtabloid.com/category/greetings',
                  'https://www.hatawtabloid.com/category/events']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }

    def parse(self, response):
        item = DemoItem()
        soup = bs(response.text,"html.parser")
        page = soup.find("span",class_="pages").text.strip().split(" ")[-1] if soup.find("span",class_="pages") else None
        if page:
            page = int(page)
            # print(page)
            for i in range(1,page+1):
                url = response.url + "page/" + str(i) + "/"
                item["request_url"] = url
                yield scrapy.Request(url,callback=self.parse_news_url,meta={"item":item})

    def parse_news_url(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        news_list = soup.find_all("article",class_ = "item-list")
        for a in news_list:
            news_url = a.select_one("h2 > a").get("href")
            # print(news_url)
            yield scrapy.Request(news_url,callback=self.parse_news,meta={"item":item})

    def parse_news(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]
        month_dict = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,"July":7,"August":8,"September":9,
                      "October":10,"November":11,"December":12}
        pub = soup.find("p", class_="post-meta").text.strip() if soup.find("p", class_="post-meta") else "0000-00-00 00:00:00"
        # print(pub)
        # pub_t = ''
        if pub:
            pub = re.compile(r'\w+').findall(pub)
            # print(pub)
            pub_t = pub[7] + "-" + str(month_dict[pub[5]]) + "-" + pub[6] + " 00:00:00"
            item["pub_time"] = pub_t
            # pub_time = time.strftime("%Y-%m-%d %H:%M:%S",pub_t)
            # print(pub_time)

        title = soup.find("h1",class_="post-title entry-title").text.strip() if soup.find("h1",class_="post-title entry-title") else None
        item["title"] = title
        image = [soup.find("div",class_="single-post-thumb").find("img").get("src")] if soup.find("div",class_="single-post-thumb") else None
        item["images"] = image
        category1 = soup.select_one("#main-content > div > article > div > p > span:nth-child(3) > a").text.strip()
        item["category1"] = category1
        item["category2"] = None
        abstract = soup.find("div",class_="entry").find("p").text.strip() if soup.find("div",class_="entry") else soup.find("div",class_="entry").find("p").text.strip()
        item["abstract"] = abstract
        body = [p.text.strip() for p in soup.find("div",class_="entry").find_all("p")] if soup.find("div",class_="entry") else None
        body = "\n".join(body)
        item["body"] = body
        print(item)
        yield item