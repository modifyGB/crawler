import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

'''
！！！该spider每个二级目录只爬了100页！！！
'''

def maharashtratimes_time_switch(time_string):
    # Updated: 10 Nov 2020, 03:03:00 PM
    time_list = re.split(" |, |:|M", time_string)
    print(time_list)
    year = time_list[4]
    month = time_list[3]
    if month == "Jan":
        month = "01"
    elif month == "Feb":
        month = "02"
    elif month == "Mar":
        month = "03"
    elif month == "Apr":
        month = "04"
    elif month == "May":
        month = "05"
    elif month == "Jun":
        month = "06"
    elif month == "Jul":
        month = "07"
    elif month == "Aug":
        month = "08"
    elif month == "Sep":
        month = "09"
    elif month == "Oct":
        month = "10"
    elif month == "Nov":
        month = "11"
    elif month == "Dec":
        month = "12"
    else:
        return None
    day = time_list[2]
    hour = time_list[5]
    min = time_list[6]
    second = time_list[7]
    if time_list[-2] == "P" and int(hour) < 10:
        hour = hour.split("0")[1]
        hour = str(int(hour) + 12)
    elif time_list[-2] == "p" and int(hour) >= 10:
        hour = str(int(hour) + 12)
    return "%s-%s-%s %s:%s:%s" % (year, month, day, hour, min, second)


class DemoSpider(scrapy.Spider):
    name = 'maharashtratimes_spider'
    website_id = 473  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://maharashtratimes.com/']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }

    def parse(self, response):
        if re.match("https://maharashtratimes.com/photogallery", response.url):
            # https://maharashtratimes.com/photogallery/politics/photolist/49655772.cms
            return

        if re.match("https://maharashtratimes.com/+$", response.url):
            soup = BeautifulSoup(response.text, "html.parser")
            category1_list = []
            menu = soup.find("nav", class_="nav_wrap").find("div", class_="items").find("ul").find_all("a")
            for c1 in menu[0:-3]:
                category1_list.append(c1.get("href"))
            for c1 in category1_list:
                yield scrapy.Request(c1, callback=self.parse)

        if re.match("https://maharashtratimes.com/+\S+\d+.cms+$", response.url) and BeautifulSoup(response.text,
                                                                                                  "html.parser").find(
                "a", class_="read_more"):
            soup = BeautifulSoup(response.text, "html.parser")
            read_more = soup.find_all("a", class_="read_more")
            for a in read_more:
                url = a.get("href")
                yield scrapy.Request(url, callback=self.parse)

        if re.match("https://maharashtratimes.com/+\S+\d+.cms+$", response.url) and BeautifulSoup(response.text,
                                                                                                  "html.parser").find(
                "a", class_="read_more") is None:
            soup = BeautifulSoup(response.text, "html.parser")
            news_url = []
            li_list = soup.find("ul", class_="col12 pd0 medium_listing").select("li") if soup.find("ul", class_="col12 pd0 medium_listing") else None
            if li_list is not None:
                for li in li_list:
                    a = li.find("a")
                    url = a.get("href") if a is not None else None
                    if url is not None:
                        news_url.append(url)

            for url in news_url:
                yield scrapy.Request(url, callback=self.parse_detail)

            page_num = 2
            while page_num <= 100:
                next_page = response.url + "?curpg=" + str(page_num)
                page_num += 1
                yield scrapy.Request(next_page, callback=self.parse)

        if re.match("https://maharashtratimes.com/+\S+?curpg=\d+$", response.url):
            soup = BeautifulSoup(response.text, "html.parser")
            news_url = []
            li_list = soup.find("ul", class_="col12 pd0 medium_listing").select("li") if soup.find("ul", class_="col12 pd0 medium_listing") else None
            if li_list is not None:
                for li in li_list:
                    a = li.find("a")
                    url = a.get("href") if a is not None else None
                    if url is not None:
                        news_url.append(url)

            for url in news_url:
                yield scrapy.Request(url, callback=self.parse_detail)

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, "html.parser")
        item['title'] = soup.find("div", class_="story-article").find("h1").text if soup.find("div",
                                                                                              class_="story-article") else None
        item['abstract'] = soup.find("div", class_="story-article").find("h2").text if soup.find("div",
                                                                                                 class_="story-article") else None
        if maharashtratimes_time_switch(soup.find("span", class_="time").text) != None:
            item['pub_time'] = maharashtratimes_time_switch(soup.find("span", class_="time").text)
        else:
            item['pub_time'] = Util.format_time()
        image_list = []
        image = soup.find("div", class_="img_wrap").find_all("img") if soup.find("div", class_="img_wrap") else None
        for img in image:
            image_list.append(img.get("src"))
        item['images'] = image_list
        body = soup.find("article")
        delete = [s.extract() for s in body("a") and body("strong")]
        item['body'] = body.text if soup.find("article") else None
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        categorymenu = soup.find("div", class_="breadcrumb").find_all("li")[:2]
        item['category1'] = categorymenu[0].text if soup.find("div", class_="breadcrumb") else None
        item['category2'] = categorymenu[1].text if soup.find("div", class_="breadcrumb") else None
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id

        yield item
