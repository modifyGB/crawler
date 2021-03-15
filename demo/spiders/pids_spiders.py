import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util


class PhilippinesSpider(scrapy.Spider):
    name = 'pids_spiders'
    website_id = 699
    language_id = 1866
    allowed_domains = ['pids.gov.ph']
    start_urls = ['https://pids.gov.ph/']

    sql = {  # sql配置
            'host': '121.36.230.205',#新的
            'user': 'dg_wsh',
            'password': 'dg_wsh',
            'db': 'dg_test_source'
        }
    #    sql = {  # sql配置
    #        'host': '192.168.235.162',
    #        'user': 'dg_wsh',
    #        'password': 'dg_wsh',
    #        'db': 'dg_test'
    #    }

    def __init__(self, time=None, *args, **kwargs):
        super(PhilippinesSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        div_list = soup.find_all("div", class_="large-3 columns button-icon-column")

        for div in div_list[2:-3]:  # 由于在“研究领域”里面包含后面刊物 新闻 活动等，直接从刊物开始
            category1 = div.select_one("a").text
            category1_url = 'https://pids.gov.ph' + div.select_one("a").get("href") if div.select("a") else None

            item['category1'] = category1

            yield scrapy.Request(category1_url, callback=self.get_year_url)

    #    def parse_detail(self, response):
    #        item = response.meta['item']
    #        soup = BeautifulSoup(response.text, 'html.parser')

    #        div = soup.find("div",class_="clickable-content")
    #        a_list = div.select("a")
    #        for a in a_list:
    #            new_list_url = category1_url + a.select_one("a").get("href") #新闻列表的url

    #        yield scrapy.Request(new_list_url, callback=self.get_year_url, meta=response.meta)

    def get_year_url(self, response):
        #        item = response.meta['item']
        soup = bs(response.text, 'html.parser')

        year_div = soup.find("div", class_="large-6 columns").select("option")
        year_list = []
        for year in year_div:
            year_list.append(year.text)
            for yearnum in year_list:
                year_url = response.url + "?year=" + yearnum  # https://pids.gov.ph/...?year=...

                yield scrapy.Request(year_url, callback=self.get_page_url)

    def get_page_url(self, response):
        #        item = response.meta['item']
        soup = bs(response.text, 'html.parser')

        page_ul = soup.find("ul", class_="pagination text-right").select("li")
        page_list = []
        for pagenum in page_ul:
            page_list.append(pagenum.text)
        max_page_num = int(page_list[-3])  # 字符转换为数字
        i = 1
        while i <= max_page_num:
            page_url = response.url + '&pagenum=' + str(i)  # https://pids.gov.ph/...?year=...&pagenum=...
            i = i + 1

            yield scrapy.Request(page_url, callback=self.get_news_url)

    def get_news_url(self, response):
        item = PhilippinesItem()
        soup = bs(response.text, 'html.parser')

        news_div = soup.find("div", class_="large-8 columns page-content-column").select("a")
        #        if(news_div.select("a"))
        news_a_list = []
        for a in news_div:
            news_a_list.append(a.get("href"))
            for temp_url in news_a_list:
                news_url = 'https://pids.gov.ph' + temp_url
        #    news_url = 'https://pids.gov.ph' + a.select_one(
        #        "#page-content > div > div.large-8.columns.page-content-column > a").get("href")
        #        else
        #            news_list = news_div.select("div",class_="row column content-list arrow-button with-icon")
        #            for news in news_list:
        #                news_url =
        if soup.find_all("div", class_="large-9 columns"):
            abstract_div = soup.find_all("div", class_="large-9 columns")
            abstract = []
            for p in abstract_div:
                abstract.append(p.find("p", class_="no-margin").text)
        else:
            None
        item['abstract'] = abstract

        if soup.find("p", class_="no-margin").select("i"):
            pub_time = Util.format_time2(soup.find("p", class_="no-margin").select_one("i").text) if soup.find("p",
                                                                                                           class_="no-margin").select_one(
                "i") else None
        elif soup.find("p", class_=""):
            pub_time = Util.format_time2(soup.find("p", class_="").select_one("i").text) if soup.find("p",
                                                                                                  class_="").select_one(
                "i") else None
        else:
            None
        item['pub_time'] = pub_time

        yield scrapy.Request(news_url, callback=self.get_news_detail, meta={'item': item})

    def get_news_detail(self, response):
        item = response.meta['item']

        soup = bs(response.text, 'html.parser')

        category2 = ''
        body = ''

        title = soup.find("div", id="page-header").select_one("h1").text if soup.find("div", id="page-header").select_one("h1") else None

        if soup.find("div", class_="pub-desc").select_one("p"):
            body = soup.find("div", class_="pub-desc").select_one("p").text
        elif soup.find("div", class_="large-8 columns page-content-column"):
            if soup.find("p", dir="ltr"):
                for span in soup.find("p", dir="ltr").select("span"):
                    body += (span.text + '\n')
            else:
                for span in soup.find("div", class_="large-8 columns page-content-column").select("span"):
                    body += (span.text + '\n')
        else:
            None
        #        body = soup.find("div",class_="pub-desc").select_one("p").text if soup.find("div",class_="pub-desc") else None

        if soup.find("div", class_="large-8 columns page-content-column").select_one("img"):
            image = soup.find("div", class_="large-8 columns page-content-column").select_one("img").get("src")
        else:
            None

        item['category2'] = category2
        item['title'] = title
        item['body'] = body
        item['image'] = image

        yield item
