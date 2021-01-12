import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests

def time_font(time_past):
    #2021-01-08T02:35:30+05:30
    #%Y-%m-%d %H:%M:%S
    big_time = time_past.split('T')[0]
    small_time = time_past.split('T')[1].split('+')[0]
    return big_time + ' ' + small_time

class hindi_news(scrapy.Spider):
    name = 'three'
    website_id = 1133  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://hindi.mykhel.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(hindi_news, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text, 'lxml')
        page_list_test = html.select('section div.os-more.clearfix')
        page_list = []
        for page_url in page_list_test:
            if page_url.find('a').get('href')[0] == '/':
                page_list.append(page_url.find('a').get('href'))
        each_page_url = []
        for i in page_list:
            url = 'https://hindi.mykhel.com/' + i
            soup = BeautifulSoup(response.text, 'lxml')
            try:
                special_url = soup.select('section div.os-more.clearfix a.os-more-b')[0].get('href')
                special_url = 'https://hindi.mykhel.com/' + special_url
                each_page_url.append(special_url)
            except:
                each_page_url.append(url)
        for h in each_page_url:
            print(h)
            yield Request(h, callback=self.parse_1)

    def parse_1(self, response):
        page_soup = BeautifulSoup(response.text, 'lxml')
        this_page_url = response.url
        next_page_url = 'https://hindi.mykhel.com/' + \
                        page_soup.select('section div.prev-next-story.clearfix.click-for-more a')[0].get('href')
        j = 0
        #j表示翻的页数
        while j < 5 and next_page_url:
            this_page_soup = BeautifulSoup(requests.get(this_page_url).text, 'lxml')
            news_url_list = this_page_soup.select('article.article_content div.tag-content-left > a')
            last_time_url = 'https://hindi.mykhel.com/' + news_url_list[-1].get('href')
            last_time = time_font(BeautifulSoup(requests.get(last_time_url).text , 'lxml').select('div.os-breadcrumb div.os-posted-by time')[0].get('datetime'))
            if self.time == None or Util.format_time3(last_time) >= int(self.time):
                for news_url in news_url_list:
                    this_url = 'https://hindi.mykhel.com/' + news_url.get('href')
                    yield Request(this_url, callback=self.parse_2)
                j = j + 1
                this_page_url = next_page_url
                try:
                    next_page_url = 'https://hindi.mykhel.com/' + \
                                this_page_soup.select('section div.prev-next-story.clearfix.click-for-more a')[0].get('href')
                except:
                    print('没有下一页了')
                    break
            else:
                self.logger.info('时间截止')
                break

    def parse_2(self, response):
        item = DemoItem()
        item = {
            'title': '',
            'body': '',
            'pub_time': '',
            'category1': '',
            'category2': '',
            'images': [],
            'abstract': ''
        }
        new_soup = BeautifulSoup(response.text, 'lxml')
        item['title'] = new_soup.select('div.os-breadcrumb > div.os-h-b h1.heading')[0].text
        for bodys in new_soup.select('div.os-sports-article-lt.os-lt p'):
            item['body'] += bodys.text
        try:
            item['abstract'] = new_soup.select('div.os-sports-article-lt.os-lt p')[0].find('strong').text
        except:
            item['abstract'] = new_soup.select('div.os-sports-article-lt.os-lt p')[0].text
        try:
            new_images_list = new_soup.select('div.os-sports-article figure > strong > img')
            for new_images in new_images_list:
                item['images'].append(new_images.get('src'))
        except:
            print("没有图片")
        item['pub_time'] = time_font(new_soup.select('div.os-breadcrumb div.os-posted-by time')[0].get('datetime'))
        item['category1'] = new_soup.select('div.os-breadcrumb div.os-breadcrumb-nav > nav > div')[1].find('span').text
        item['category2'] = new_soup.select('div.os-breadcrumb div.os-breadcrumb-nav > nav > div')[2].find('span').text
        yield item