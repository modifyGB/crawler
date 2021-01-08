import scrapy
import time
from bs4 import BeautifulSoup as bs
import datetime
import re
from demo.items import DemoItem
from demo.util import Util

class Balita1Spider(scrapy.Spider):
    name = 'balita1'
    allowed_domains = ['balita.ph']
    start_urls = [#'https://balita.ph/',
                  'https://balita.ph/category/news/',
                  'https://balita.ph/category/world/',
                  'https://balita.ph/category/economy/',
                  'https://balita.ph/category/entertainment/',
                  'https://balita.ph/category/sports/',
                  'https://balita.ph/category/lifestyle/',
                  'https://balita.ph/category/technology/',
                  'https://balita.ph/category/opinion/']
    website_id = 498
    language_id = 1866
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }
    def parse(self, response):
        item = DemoItem()
        soup = bs(response.text,"html.parser")

        category2_url =[li.find("a").get("href") for li in soup.find_all("li","td-pulldown-filter-item")]
        # print(category2_url)
        for url in category2_url:
            yield scrapy.Request(url,callback=self.parse_news_page,meta={"item":item})

    def parse_news_page(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        l_list = soup.find_all("h3","entry-title td-module-title") if soup.find_all("h3","entry-title td-module-title") else None
        if l_list:
            for l in l_list:
                news_url = l.find("a").get("href")
                category1 = soup.select_one("#td-outer-wrap > div > div > div > div > h1").text.strip()
                item["category1"] = category1
                category2 = soup.find("div", "td-pulldown-filter-display-option").select_one("div").text.strip()
                item["category2"] = category2
                yield scrapy.Request(news_url,callback=self.parse_news,meta={"item":item})

        page = soup.find("span","pages").text.strip().split(" ")[-1] if soup.find("span","pages") else None
        if page:
            for i in range(1,int(page)+1):
                r_url = response.url.rsplit("/",1)
                url = r_url[0] + "/page/" + str(i) + "/" + r_url[1]
                request_url = url
                yield scrapy.Request(url,callback=self.parse_news_list,meta={"item":item})
        else:
            request_url = response.url
            yield scrapy.Request(response.url,callback=self.parse_news_list,meta={"item":item})

    def parse_news_list(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        category1 = soup.select_one("#td-outer-wrap > div > div > div > div > h1").text.strip()
        item["category1"] = category1
        category2 = soup.find("div", "td-pulldown-filter-display-option").select_one("div").text.strip()
        item["category2"] = category2

        div_list = soup.find_all("div","td-block-span6")

        for div in div_list:
            news_url = div.find("h3","entry-title td-module-title").find("a").get("href")
            yield scrapy.Request(news_url,callback=self.parse_news,meta={"item":item})

    def parse_news(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        pub_time = soup.find("time","entry-date updated td-module-date").text.strip() if soup.find("time","entry-date updated td-module-date") else "0000-00-00 00:00:00"
        if pub_time:
            pub = ''
            for t in re.compile(r'\w+').findall(pub_time):
                pub = pub + t
            pub_time = datetime.datetime.strptime(pub, '%B%d%Y')
        item["pub_time"] = pub_time
        cole_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        title = soup.find("h1","entry-title").text.strip() if soup.find("h1","entry-title") else None
        item["title"] = title
        div = soup.find("div","td-post-content tagdiv-type")
        images = [ img.get("src") for img in div.find_all("img")] if div.find_all("img") else None
        abstract = div.find("p").text.strip()
        body = [p.text.strip() for p in div.find_all("p")] if div.find_all("p") else None
        if abstract:
            body = "\n".join(body)
        else:
            abstract = div.find("h4").text.strip()
            body = [h.text.strip() for h in div.find_all("h4")] if div.find_all("h4") else None
            body = "\n".join(body)
        item["images"] = images
        item["abstract"] = abstract
        item["body"] = body
        md5 = response.url.split("/")[-2]
        print(item)
        yield item

