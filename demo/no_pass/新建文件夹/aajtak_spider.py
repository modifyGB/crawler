import scrapy
import requests
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


def aajtak_time_switch(time_string):
    # (अपडेटेड 14 नवंबर 2020, 3:50 PM IST)
    time_list = re.split(" |,|M|:", time_string)
    hour = time_list[-5]
    min = time_list[-4]
    if int(hour) < 10 and time_list[-3] == "P":
        hour = str(int(hour) + 12)
    if int(hour) < 10 and time_list[-3] == "A":
        hour = "0" + hour
    return "%s:%s:00" % (hour, min)


class DemoSpider(scrapy.Spider):
    name = 'aajtak_spider'
    website_id = 501  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.aajtak.in/']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }
    no_list = [
        "photo", "videos", "elections", "coronavirus-covid-19-outbreak", "rate-card", "anchors",
        "india-today-plus", "tez", "trending"
    ]
    type2_list = [
        "fact-check", "world"
    ]

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category1_list_type1 = []
        category1_list_type2 = []
        category1_list_type3 = []
        li_list = soup.find("div", class_="navigation-container").find("nav").find("ul", class_="at-menu").find_all(
            "li")
        for li in li_list[2:]:
            url = li.find("a").get("href")
            if url.rsplit("/", 1)[-1] == "events":
                category1_list_type3.append(url)
            elif url.rsplit("/", 1)[-1] not in self.no_list:
                category1_list_type1.append(url)
            elif url.rsplit("/", 1)[-1] in self.type2_list:
                category1_list_type2.append(url)
        for url in category1_list_type1:
            yield scrapy.Request(url, callback=self.parse_cate1_type1)
        for url in category1_list_type2:
            yield scrapy.Request(url, callback=self.parse_cate1_type2)

    def parse_cate1_type1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category2_list = []
        widget_more = soup.find_all("div", class_="widget-more")
        for w in widget_more:
            url = w.find("a").get("href")
            category2_list.append(url)
        if response.url.rsplit("/", 1)[-1] == "india":
            # india第一目录下有Load-more
            response2 = requests.get("https://www.aajtak.in/ajax/load-more-widget?id=1&type=story/photo_gallery/video"
                                     "/breaking_news&path=/india")
            soup2 = BeautifulSoup(response2.text, features="lxml")
            h2_list = soup2.find_all("h2")
            for h2 in h2_list:
                url = h2.find("a").get("href")
                category2_list.append(url)

        for url in category2_list:
            yield scrapy.Request(url, callback=self.parse_catgory2)

    def parse_cate1_type2(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        load_page = 1

        top_news = soup.find("div", class_="content-area").find_all("div", class_="mano-ranj-container")
        for div in top_news:
            a_list = div.find_all("a")
            for a in a_list:
                news_url.append(a.get("href"))
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_catgory2)
        while 1:
            load_more_url = "https://www.aajtak.in/ajax/load-more-special-listing?id=)" + str(load_page) + "&type" \
                                                                                                           "=story/photo_gallery/video/breaking_news&path=/" + \
                            response.url.rsplit("/", 1)[-1]
            load_response = requests.get(load_more_url)
            load_soup = BeautifulSoup(load_response.text, features="lxml")
            a_list = load_soup.find_all("a")
            for a in a_list:
                url = a.get("href").replace("\\", "").replace('"', '')
                if url.split("/", 5)[4] != "video":
                    # https://www.aajtak.in/tez/video/america-worst-hit-from-coronavirus-pandemic-1160999-2020-11-11
                    yield scrapy.Request(url, callback=self.parse_catgory2)
            if re.split('"is_load_more":|}', load_response.text)[1] == 1:
                load_page += 1
            else:
                break

    def parse_catgory2(self, response):
        after_words = response.url.split("/", 3)[-1]  # load_more请求页后缀
        # load_more请求页模板：https://www.aajtak.in/ajax/load-more-widget?id=1&type=story/photo_gallery/video/breaking_news&path=/india/uttarakhand
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        content = soup.find_all("div", class_="widget-listing")
        for con in content:
            url = con.find("a").get("href")
            if url.split("/", 6)[5] != "video":
                news_url.append(url)
        for news in news_url:
            yield scrapy.Request(news, callback=self.parse_detail)
        load_page = 1
        while 1:
            load_more_url = "https://www.aajtak.in/ajax/load-more-widget?id=" + str(load_page) + "&type=story" \
                                                                                                 "/photo_gallery/video/breaking_news&path=/india/uttarakhand "
            load_response = requests.get(load_more_url)
            load_soup = BeautifulSoup(load_response.text, features="lxml")
            load_soup_text = load_soup.text.strip()
            load_news_url = []
            if load_soup_text == "":
                break
            else:
                h2_list = load_soup.find_all("h2")
                for h2 in h2_list:
                    url = h2.find("a").get("href")
                    if url.split("/", 6)[5] != "video":
                        load_news_url.append(url)
            for url in load_news_url:
                yield scrapy.Request(url, callback=self.parse_detail)
            load_page += 1

    def parse_detail(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        item = DemoItem()
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        category = soup.find("div", class_="bradcum").find_all("a") if soup.find("div", class_="bradcum") else None
        item['category1'] = category[-2].text.strip() if category else None
        item['category2'] = category[-1].text.strip() if category else None
        item['title'] = soup.find("div", class_="story-heading").text.strip() if soup.find("div",
                                                                                           class_="story-heading") else None
        item['abstract'] = soup.find("div", class_="sab-head-tranlate-sec").text.strip() + "\n" if soup.find("div",
                                                                                                             class_="sab-head-tranlate-sec") else ""
        abstract_list = soup.find("div", class_="StoryLhsbody").find_all("li") if soup.find("div",
                                                                                            class_="StoryLhsbody") else None
        if abstract_list is not None:
            for li in abstract_list:
                item['abstract'] += "\n" + li.text.strip()
        datelist = response.url.rsplit("-", 3)[-3:]
        pub_time = soup.find("div", class_="brand-detial-main").find_all("li")[-1].text.strip()
        item['pub_time'] = "%s-%s-%s " % (datelist[0], datelist[1], datelist[2]) + aajtak_time_switch(pub_time)
        body = ""
        body_list = soup.find("div", class_="text-formatted field field--name-body field--type-text-with-summary "
                                            "field--label-hidden field__item").children if soup.find("div",
                                                                                                     class_="text-formatted field field--name-body field--type-text-with-summary "
                                                                                                            "field--label-hidden field__item") else None
        for b in body_list:
            if b.name == "div":
                break
            else:
                body += BeautifulSoup(str(b), features="lxml").text.strip() + "\n"
        item['body'] = body
        img_list = []
        images = soup.find("div", class_="main-img").find_all("img")
        for img in images:
            img_list.append(img.get("data-src"))
        item['images'] = img_list
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id

        yield item
