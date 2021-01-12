import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests

def time_font(time_past):
    #%Y-%m-%d %H:%M:%S
    time_past = time_past.strip()
    year = time_past.split(' ')[2]
    month = time_past.split(' ')[0]
    day = time_past.split(' ')[1]
    second = '00'
    hour = time_past.split(' ')[3].split(":")[0]
    minute = time_past.split(' ')[3].split(":")[1]
    half = time_past.split(' ')[4]
    if half == 'PM':
        hour = int(hour) + 11
    if month == 'Jan':
        month = '01'
    elif month == 'Feb':
        month = '02'
    elif month == 'Mar':
        month = '03'
    elif month == 'Apr':
        month = '04'
    elif month == 'May':
        month = '05'
    elif month == 'Jun':
        month = '06'
    elif month == 'Jul':
        month = '07'
    elif month == 'Aug':
        month = '08'
    elif month == 'Sep':
        month = '09'
    elif month == 'Oct':
        month = '10'
    elif month == 'Nov':
        month = '11'
    else:
        month = '12'
    return year + '-' + month + '-' + day + ' ' + str(hour) + ':' + month + ':' + second

class newstracklive(scrapy.Spider):
    name = 'four'
    website_id = 1134  # 网站的id(必填)
    language_id = 1740  # 所用语言的id
    start_urls = ['https://www.newstracklive.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(newstracklive, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text, 'lxml')
        test_page_list = []
        page_list = []
        # 解析一级目录
        test_page_list = html.select('div.collapse.navbar-collapse ul li')
        for i in range(3):
            page_list.append(test_page_list[i].find('a').get('href'))
        test_page_list.clear()
        test_page_list.extend(
            html.select('div.collapse.navbar-collapse ul li.dropdown ul.dropdown-menu.text-capitalize li'))
        for test_page in test_page_list:
            page_list.append(test_page.find('a').get('href'))
        for i in page_list:
            yield Request(i , callback=self.parse_1)

    def parse_1(self , response ,  **kwargs):
        page_soup = BeautifulSoup(response.text, 'lxml')
        category1 = page_soup.select('div.main-title-outer.pull-left div.main-title')[0].text.strip()
        next_page_url = 'https://www.newstracklive.com/entertainment-news/television-news/' + \
                        page_soup.select('div.nt_detailview div.ntdv_pagination > ul > li')[-1].find('a').get(
                               'href')
        this_page_url = response.url
        j = 0
        while j < 1 and next_page_url:
            this_page_soup = BeautifulSoup(response.text, 'lxml')
            news_url_list = this_page_soup.select(
                'div.container div.col-sm-16.business.wow.fadeInDown.animated div.row div.col-md-16.col-sm-16 div.col-md-4.col-sm-8.col-xs-16 > div.topic.nt_topic > a')
            last_new_url = news_url_list[-1].get('href')
            last_new_time = time_font(BeautifulSoup(requests.get(last_new_url).text,'lxml').select('div.text-danger.sub-info-bordered div.time')[0].text)
            if self.time == None or Util.format_time3(last_new_time) >= int(self.time):
                for news_url in news_url_list:
                    item = DemoItem()
                    item = {
                        'title': '','body': '','pub_time': '','category1': '','category2': '','images': [],'abstract': ''
                    }
                    item['category1'] = category1
                    item['category2'] = category1
                    yield Request(news_url, callback=self.parse_2 , meta={'item' : item})
                j = j + 1
                this_page_url = next_page_url
                try:
                    next_page_url = 'https://www.newstracklive.com/entertainment-news/television-news/' + \
                                    this_page_soup.select('div.nt_detailview div.ntdv_pagination > ul > li')[-1].find(
                                        'a').get('href')
                except:
                    print('没有下一页了')
                    break
            else:
                self.logger.info('时间截止')
                break

    def parse_2(self, response):
        item = response.meta['item']
        new_soup = BeautifulSoup(response.text , 'lxml')
        item['title'] = \
        new_soup.select('div.sec-topic.nt_detailview.col-sm-16.wow.fadeInDown.animated div.col-sm-16.sec-info > h1')[
            0].text
        for bodys in new_soup.find_all('p', style='text-align: justify;'):
            item['body'] += bodys.text
        item['abstract'] = new_soup.find_all('p', style='text-align: justify;')[0].text
        try:
            new_images_list = new_soup.select(
                'div.sec-topic.nt_detailview.col-sm-16.wow.fadeInDown.animated div.ntdv_imgcon > img')
            for new_images in new_images_list:
                item['images'].append(new_images.get('src'))
        except:
            print("没有图片")

        item['pub_time'] = time_font(new_soup.select('div.text-danger.sub-info-bordered div.time')[0].text)
        yield item