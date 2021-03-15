import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util


class PnaSpider(scrapy.Spider):
    name = 'pna'
    website_id = 1156
    language_id = 1866
    allowed_domains = ['pna.gov.ph']
    start_urls = ['http://www.pna.gov.ph/']

    sql = {  # sql配置
            'host': '121.36.230.205',#新的
            'user': 'dg_wsh',
            'password': 'dg_wsh',
            'db': 'dg_test_source'
        }
    def __init__(self, time=None, *args, **kwargs):
        super(PnaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        div = soup.find("div", class_="wrapper wrapper-foot")
        li_list = div.select("div > div > div > div > ul > li")
        for li in li_list[1:]: #去掉Home
            category1 = li.select_one("a").text.strip(' \n')
            item['category1'] = category1

            category1_url = "http://www.pna.gov.ph" + li.select_one("a").get("href")
            yield scrapy.Request(category1_url, callback=self.get_news_url, meta={"item": item})

    def get_news_url(self, response):
        soup = bs(response.text, 'html.parser')

        div = soup.find("div", class_="articles")
        div_list = div.find_all("div", class_="article media")
        for d in div_list:
            news_url = "http://www.pna.gov.ph" + d.select_one("a").get("href")
            yield scrapy.Request(news_url, callback=self.get_news_detail)

        if self.time == None or Util.format_time3(Util.format_time4(soup.select("span", class_="date")).get_text()) >= int(self.time):
            nav = soup.find("nav", class_="pagination-area")
            li_list = nav.select("ul > li")
            next_url = "http://www.pna.gov.ph" + li_list[-2].select_one("a").get("href") if li_list[-2].select_one("a").get("href") else None #用'>'来进行下一页操作
            if next_url:
                yield scrapy.Request(next_url, meta=response.meta, callback=self.get_news_url)
        else:
            self.logger.info('时间截止')

    def get_news_detail(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        title = soup.find("h1").text if soup.find("h1") else None

        pub_time_div = soup.find("div", class_="col-sm-6 cell-1")
        pub_time = Util.format_time4(pub_time_div.find("span", class_="date").get_text()) if pub_time_div.find("span", class_="date") else None
        #January 13, 2021, 1:19 pm

        if soup.find("figure", class_="image align-right"):
            image_figure = soup.find("figure", class_="image align-right")
            image = image_figure.select_one("img").get("src")
        else:
            None

        body = ''
        p_list = soup.find("div", class_="page-content").select("p")
        for p in p_list[1:]:
            body += (p.text + '\n')

        abstract = ''
        category2 = ''

        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image
        item["body"] = body
        item["abstract"] = abstract
        item["category2"] = category2

        yield item
