#网站被渲染了

import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util

class PolicyAimEduSpider(scrapy.Spider):
    name = 'policy_aim_edu'
    website_id=700
    language_id = 1866
    allowed_domains = ['policy.aim.edu']
    start_urls = ['http://policy.aim.edu//']
    sql = {  # sql配置
            'host': '121.36.230.205',#新的
            'user': 'dg_wsh',
            'password': 'dg_wsh',
            'db': 'dg_test_source'
        }
    def __init__(self, time=None, *args, **kwargs):
        super(PolicyAimEduSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        div = soup.find("div", id="contentContainer")
        li_list = div.select("ul > li")
        for li in li_list[3:-2]:  # 只要 Research and Knowledge Materials 和 Event
            category1 = li.select_one("a").text

            if li.select_one("a").text == "Programs":
                pass
            elif li.select_one("a").text == "Research and Knowledge Materials":
                item['category1'] = category1
                li_temp_list = li.select("ul > li")
                for li_temp in li_temp_list:
                    category2 = li_temp.select_one("a").text
                    item['category2'] = category2
                    category_url = li_temp.select_one("a").get("href") if li_temp.select_one("a") else None
                    yield scrapy.Request(category_url, callback=self.get_news_detail, meta={"item": item})
            else:
                item['category1'] = category1
                category_url = li.select_one("a").get("href") if li.select_one("a").get("href") else None
                yield scrapy.Request(category_url, callback=self.get_news_url, meta={"item": item})

    def get_news_url(self, response):
        soup = bs(response.text, 'html.parser')

        tr_list = soup.find_all("tr")
        for tr in tr_list:
            td_list = soup.find_all("td")
            for td in td_list:
                if td.select_one("a"):
                    news_url = td.select_one("a").get("href")
                    temp_url = news_url.rsplit("/", 3)
                    if temp_url[0] == "http://policy.aim.edu/blog":
                        news_url = news_url
                    else:
                        news_url = "http://policy.aim.edu/" + news_url
                    yield scrapy.Request(news_url, callback=self.get_news_detail)
                else:
                    pass

    def get_news_detail(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        if soup.find("h3"):
            title = soup.find("h3").get_text()
        else:
            title = soup.find("h1").get_text()

        if soup.find("img"):
            image = soup.find("img").get("src")
        else:
            image = None

        if soup.find("div", class_="date"):
            pub_time = soup.find("div", class_="date").select_one("span").get_text()
        else:
            time_p = soup.find("p", class_="note note-list")
            span_list = time_p.find_all("span")
            posted_time = span_list[1].get_text().strip('"')
            pub_time_list = posted_time.rsplit(":", 1)
            pub_time = pub_time_list[1]

        if soup.find("div", class_="abstract-text"):# 网页被渲染了爬不到东西
            abstract_p = soup.find_all("p")
            abstract = abstract_p[0].text
        else:
            abstract = None

        body = ''
        if soup.find("div", class_="body"):
            p_list = soup.find("div", class_="body").select("p")
            for p in p_list[1:-3]:
                body += (p.text + '\n')
        else:
            None

        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image
        item["abstract"] = abstract
        item["body"] = body
        yield item

