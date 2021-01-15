
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#将爬虫类名和name字段改成对应的网站名
class aajkaSpider(scrapy.Spider):
    name = 'aajka'
    website_id = 966  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://aajka-samachar.in/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(aajkaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.find('ul', class_="nav-menu navbar-nav d-lg-block").select('li a') if soup.find('ul',
                                                                                                          class_="nav-menu navbar-nav d-lg-block").select(
            'li a') else None
        for category in categories:
            category_hrefList.append(category.get("href"))
            # category_nameList.append(category.text.replace('\n', ''))
        del category_hrefList[0]
        category_hrefList.pop()
        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        if self.time == None or Util.format_time3(time_adjustment(soup.select('div.date a')[-1].text)) >= int(self.time):
            articles = soup.select('h2.entry-title a')
            article_hrefs = []
            for article in articles:
                article_hrefs.append(article.get('href'))

            for detail_url in article_hrefs:
                yield Request(detail_url, callback=self.parse_detail)
        else:
            self.logger.info("时间截止")
        # if soup.select_one('li.nav-previous a').get('href'):
        #     yield Request(soup.select_one('li.nav-previous a').get('href'), callback=self.parse_category)

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        p_list = soup.select('div.entry-content p') if soup.select('div.entry-content p') else None
        content_list = []
        for p in p_list:
            if p.find("a"):
                continue
            content_list.append(p.text)
        content = "\n".join(content_list)
        item['body'] = content
        temp_time = soup.select_one('div.date a').text if soup.select_one('div.date a').text else None
        adjusted_time = time_adjustment(temp_time)
        item['pub_time'] = adjusted_time
        item['abstract'] = soup.select_one('div.entry-content p').text if soup.select_one(
            'div.entry-content p').text else None
        news_categories = soup.select('div.cat-links a') if soup.select('div.cat-links a') else None
        item['category1'] = news_categories[0].text
        item['category2'] = news_categories[1].text
        item['title'] = soup.select_one('h1.entry-title').text if soup.select_one('h1.entry-title').text else None
        yield item

def time_adjustment(input_time):
    get_year = input_time.split(", ")
    month_day = get_year[0].split(" ")
    if month_day[0] == "January":
        month = "01"
    elif month_day[0] == "February":
        month = "02"
    elif month_day[0] == "March":
        month = "03"
    elif month_day[0] == "April":
        month = "04"
    elif month_day[0] == "May":
        month = "05"
    elif month_day[0] == "June":
        month = "06"
    elif month_day[0] == "July":
        month = "07"
    elif month_day[0] == "August":
        month = "08"
    elif month_day[0] == "September":
        month = "09"
    elif month_day[0] == "October":
        month = "10"
    elif month_day[0] == "November":
        month = "11"
    elif month_day[0] == "December":
        month = "12"
    else:
        month = "None"

    if int(month_day[1]) < 10:
        day = "0" + month_day[1]
    else:
        day = month_day[1]

    return "%s-%s-%s" % (get_year[1], month, day) + " 00:00:00"
