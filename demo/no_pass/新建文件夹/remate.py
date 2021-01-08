import scrapy
import time
from bs4 import BeautifulSoup as bs
import datetime
import re
from demo.items import DemoItem
from demo.util import Util


class RemateSpider(scrapy.Spider):
    name = 'remate'
    allowed_domains = ['www.remate.ph']
    start_urls = ['https://www.remate.ph/news/',
                  'https://www.remate.ph/sports/',
                  'https://www.remate.ph/lifestyle/',
                  'https://www.remate.ph/tech-trend/',
                  'https://www.remate.ph/entertainment/',
                  'https://www.remate.ph/opinion/']

    website_id = 533
    language_id = 2117
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }

    def parse(self, response):
        item = DemoItem()
        soup = bs(response.text,"html.parser")

        a_list = ["https://www.remate.ph" + a.find("a").get("href") for a in soup.find_all("div","vc_btn3-container vc_btn3-center")]
        if a_list:
            for url in a_list:
                yield scrapy.Request(url,callback=self.parse_page,meta={"item":item})
        else:
            a_list2 = ["https://www.remate.ph" + a.get("href") for a in soup.find_all("a","vc_btn3 vc_btn3-shape-square btn btn-sm btn-modern btn-primary")]
            for url2 in a_list2:
                print(url2)
                yield scrapy.Request(url2, callback=self.parse_page, meta={"item": item})

    def parse_page(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        page = soup.find("div","pagination").find_all("a")[-2].get("href").split("/")[-2]
        for i in range(1,int(page)+1):
            page_url = response.url + "page/" + str(i) + "/"
            yield scrapy.Request(page_url,callback=self.parse_news_list,meta={"item":item})

    def parse_news_list(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        h_list = soup.find_all("h2","entry-title")

        category1 = soup.select_one("body > div > section > div > div > div > div > ul > li:nth-child(2) > a > span").text.strip() if soup.select_one("body > div > section > div > div > div > div > ul > li:nth-child(2) > a > span") else None
        category2 = soup.select_one("body > div > section > div > div > div > div > ul > li:nth-child(3)").text.strip() if soup.select_one("body > div > section > div > div > div > div > ul > li:nth-child(3)") else None
        item["category1"] = category1
        item["category2"] = category2
        for h in h_list:
            request_url = h.find("a").get("href")
            yield scrapy.Request(request_url,callback=self.parse_news,meta={"item":item})


    def parse_news(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        response_url = response.url
        # div = soup.find("div","main-content col-lg-9").select_one("div > article")
        pub_time = soup.select_one("#content > article > div.post-content > div > span").text.strip() if soup.select_one("#content > article > div.post-content > div > span") else "0000-00-00 00:00:00"
        if pub_time:
            pub = re.compile(r'\w+').findall(pub_time)
            pu = pub[-1]
            pub.pop()
            p_time = ''
            for p in pub:
                p_time += p
            pub_time = str(datetime.datetime.strptime(p_time,'%B%d%Y%I%M'))
            # print(pub_time)
        item["pub_time"] = pub_time
        cole_time = time.strftime("%Y-%m-%d %H:%M:S", time.localtime(int(time.time())))
        title = soup.select_one("#content > article > h1").text.strip() if soup.select_one("#content > article > h1") else None
        item["title"] = title
        images = [img.get("src") for img in soup.select_one("#content > article").find_all("img")] if soup.select_one("#content > article").find_all("img") else None
        item["images"] = images
        abstract = soup.select_one("#content > article").find("h4").text.strip() if soup.select_one("#content > article").find("h4") else None
        body = [h.text.strip() for h in soup.select_one("#content > article").find_all("h4")] if soup.select_one("#content > article").find_all("h4") else None
        if abstract:
            body = "\n".join(body)
        else:
            abstract = soup.select_one("#content > article").find("p").text.strip() if soup.select_one("#content > article").find("p") else None
            body = [p.text.strip() for p in soup.select_one("#content > article").find_all("p")] if soup.select_one("#content > article").find_all("p") else None
            body = "\n".join(body)
        item["abstract"] = abstract
        item["body"] = body
        print(item)
        yield item

