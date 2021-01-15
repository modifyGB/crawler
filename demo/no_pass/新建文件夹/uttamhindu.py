
# 此文件包含的头文件不要修改
import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime

#将爬虫类名和name字段改成对应的网站名
class uttamhinduSpider(scrapy.Spider):
    name = 'uttamhindu'
    website_id = 995 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.uttamhindu.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_lhl',
        'password': 'dg_lhl',
        'db': 'dg_test'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(uttamhinduSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.find('ul', class_="nav navbar-nav").select('li a') if soup.find('ul', class_="nav navbar-nav").select('li a') else None
        categories.pop(0)
        for category in categories:
            category_hrefList.append(category.get('href'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")

        articles = soup.select('div.cut-content a')
        article_hrefs = []
        for article in articles:
            article_hrefs.append(article.get('href'))
        for detail_url in article_hrefs:
            yield Request(detail_url, callback=self.parse_detail)


        check_soup = BeautifulSoup(requests.get(article_hrefs[-1]).content)     #不加content会出错，原因是因为这里的wb_data是requests对象，无法用BeautifulSoup解析
        temp_time = check_soup.select_one('div.full-heading p').text if check_soup.select_one('div.full-heading p').text else None
        adjusted_time = time_adjustment(temp_time).strip()
        if self.time == None or Util.format_time3(adjusted_time) >= int(self.time):
            if soup.select('ul.pagination li a')[-1].get('href') == "javascript:void(0);":
                self.logger.info("最后一页了")
            else:
                yield Request(soup.select('ul.pagination li a')[-1].get('href'), callback=self.parse_category)
        else:
            self.logger.info("时间截止")


    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        temp_time = soup.select_one('div.full-heading p').text if soup.select_one('div.full-heading p').text else None
        item['pub_time'] = time_adjustment(temp_time)
        image_list = []
        imgs = soup.find('div', class_="item active").select_one('img').get('src') if soup.find('div', class_="item active").select_one('img').get('src') else None
        if imgs:
            for img in imgs:
                image_list.append(img)
            item['images'] = image_list
        p_list = []
        all_p = soup.select('div.full-news p') if soup.select('div.full-news p') else None
        all_p.pop()
        all_p.pop(0)
        all_p.pop(0)
        for p in all_p:
            if p.select('img'):
                for i in p.select('img'):
                    image_list.append(i.get('src'))
                    item['images'] = image_list

        for paragraph in all_p:
            if paragraph.text:
                p_list.append(paragraph.text)
        body = '\n'.join(p_list)


        item['abstract'] = p_list[0]
        item['body'] = body
        item['category1'] = soup.select_one('div.category-title').text if soup.select_one('div.category-title').text else None

        item['title'] = soup.select_one('div.full-heading h2').text if soup.select_one('div.full-heading h2').text else None
        yield item



def time_adjustment(input_time):
    input_time2 = input_time.replace('Publish Date: ', '')
    time_elements = input_time2.split(" ")
    hms = time_elements[3].split(":")

    if time_elements[0] == "January":
        month = "01"
    elif time_elements[0] == "February":
        month = "02"
    elif time_elements[0] == "March":
        month = "03"
    elif time_elements[0] == "April":
        month = "04"
    elif time_elements[0] == "May":
        month = "05"
    elif time_elements[0] == "June":
        month = "06"
    elif time_elements[0] == "July":
        month = "07"
    elif time_elements[0] == "August":
        month = "08"
    elif time_elements[0] == "September":
        month = "09"
    elif time_elements[0] == "October":
        month = "10"
    elif time_elements[0] == "November":
        month = "11"
    elif time_elements[0] == "December":
        month = "12"
    else:
        month = "None"

    # if int(time_elements[1]) < 10:
    #     day = "0" + time_elements[1]
    # else:
    #     day = time_elements[1]
    output_time = "%s-%s-%s %s:%s:%s" % (time_elements[2], month, time_elements[1], hms[0], hms[1], hms[2])

    if output_time[-2:] == "am":
        return output_time.strip()[:-2]
    elif output_time[-2:] == "pm":
        adjusted_time = "%s-%s-%s %s:%s:%s" % (time_elements[2], month, time_elements[1], str(int(hms[0]) + 12), hms[1], hms[2])
        return adjusted_time.strip()[:-2]