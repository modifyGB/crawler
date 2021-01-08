import re
import time
import scrapy
from bs4 import BeautifulSoup as bs
import datetime
from demo.util import Util
from demo.items import DemoItem

class KickerdailySpider(scrapy.Spider):
    name = 'kickerdaily'
    allowed_domains = ['kickerdaily.com']
    start_urls = [#'http://kickerdaily.com/',
                  'https://kickerdaily.com/posts/category/tagalog/',
                  'https://kickerdaily.com/posts/category/philippines/',
                  'https://kickerdaily.com/posts/category/world/',
                  'https://kickerdaily.com/posts/category/entertainment-world/',
                  'https://kickerdaily.com/posts/category/social-news/']
    website_id = 496
    language_id = 1880
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }
    def parse(self, response):
        soup = bs(response.text,"html.parser")
        item = DemoItem()
        category1 = soup.find("h1",class_="page-title").text.strip()
        print(category1)
        item["category1"] = category1
        page = soup.find_all("a",class_="page-numbers")[-2].text.strip()
        print(page)
        for i in range(1,int(page)+1):
            url = response.url + "page/" + str(i) + "/"
            yield scrapy.Request(url,callback=self.parse_news_url,meta={"item":item})

    def parse_news_url(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]

        url_list = soup.find_all("h3",class_="entry-title mh-posts-list-title")
        for h in url_list:
            news_url = h.find("a").get("href")
            # print(news_url)
            yield scrapy.Request(news_url,callback=self.parse_news,meta={"item":item})

    def parse_news(self,response):
        soup = bs(response.text,"html.parser")
        item = response.meta["item"]
        pub_time = soup.find("span","entry-meta-date updated").find("a").text.strip() if soup.find("span","entry-meta-date updated") else "0000-00-00 00:00:00"
        # print(pub_time)
        if pub_time:
            pub = ''
            for t in re.compile(r'\w+').findall(pub_time):
                pub = pub + t
            # print(pub)
            pub_time = time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.strptime(pub,'%B%d%Y').timetuple())
            item["pub_time"] = pub_time
        div = soup.find("div",class_="entry-content clearfix")
        images = [img.get("src") for img in div.find_all("img")] if div.find_all("img") else None
        # print(images)
        item["images"] = images
        title = soup.find("h1",class_="entry-title").text.strip()
        # print(title)
        item["title"] = title
        abstract = div.find_all("li")[0].text.strip() if div.find_all("li") else div.find("p").text.strip()
        # abstract = "\n".join(abstract)
        # print(abstract)
        item["abstract"] = abstract
        body = [p.text.strip() for p in div.find_all("p")] if div.find_all("p") else None
        body = "\n".join(body)
        # print(body)
        item["body"] = body

        print(item)
        yield item