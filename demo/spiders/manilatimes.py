import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util

class ManilatimesSpider(scrapy.Spider):
    name = 'manilatimes'
    website_id = 847
    language_id = 1866
    allowed_domains = ['www.manilatimes.net']
    start_urls = ['http://www.manilatimes.net/']

    sql = {  # sql配置
            'host': '121.36.230.205',#新的
            'user': 'dg_wsh',
            'password': 'dg_wsh',
            'db': 'dg_test_source'
        }
    def parse(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        div = soup.find("div", class_="tdb-menu-items-pulldown")
        li_list = div.select("ul > li")
        for li in li_list:
            category1 = li.select_one("a").text
            item['category1'] = category1

            get_a = li.select_one("a").get("href").split("/",1)
            if get_a[0]=="https:" or get_a[0]=="http:":
                pass
            else:
                category1_url = "http://www.manilatimes.net/" + get_a[1]
            yield scrapy.Request(category1_url, callback=self.get_news_url, meta={"item": item})

    def get_news_url(self, response):
        soup = bs(response.text, 'html.parser')

        div_list = soup.find_all("div", class_="tdb_module_loop td_module_wrap td-animation-stack")
        for div in div_list:
            news_url = div.find("h3", class_="entry-title td-module-title").select_one("a").get("href")
            yield scrapy.Request(news_url, callback=self.get_news_detail)

        div = soup.find("div", class_="page-nav td-pb-padding-side")
        a_list = div.select("a")
        temp_last_page = a_list[-2].text.split(",")
        last_page_num = int(temp_last_page[0] + temp_last_page[1])
        temp = a_list[-1].get("href").rsplit("/", 3)
        first_page_url = temp[0]
        page_num = 1
        if self.time == None or Util.format_time3(Util.format_time4(soup.select("time", class_="entry-date updated td-module-date").get_text())) >= int(self.time):
            while page_num <= last_page_num:
                page_num += 1
                next_url = first_page_url + "/page/" + str(page_num) + "/"

            if next_url:
                yield scrapy.Request(next_url, meta=response.meta, callback=self.get_news_url)
        else:
            self.logger.info('时间截止')

    def get_news_detail(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        title = soup.find("h1", class_="tdb-title-text").text if soup.find("h1", class_="tdb-title-text") else None

        pub_time = Util.format_time4(soup.find("time", class_="entry-date updated td-module-date").text) if soup.find("time", class_="entry-date updated td-module-date") else None

        body = ''
        p_list = soup.find_all("p")
        for p in p_list[:-5]:
            body += (p.text + '\n')

        image = ''
        abstract = ''
        category2 = ''

        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image
        item["body"] = body
        item["abstract"] = abstract
        item["category2"] = category2

        yield item