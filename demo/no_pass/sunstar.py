import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class sunstarSpider(scrapy.Spider):
    name = 'sunstar'
    website_id = 443 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.sunstar.com.ph/Philippines']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_admin',
        'password' : 'dg_admin',
        'db' : 'dg_crawler'
    }

    def parse(self, response):
        html = BeautifulSoup(response.text)
        if response.url == 'https://www.sunstar.com.ph/Philippines':
            for i in html.select('.tablecenter > a')[0:8]:
                yield Request(i.attrs['href'])
        elif re.findall(r'https://www.sunstar.com.ph/article/\d+/\S+?/\S+?/\S+?',response.url) != []:
            item = DemoItem()
            list = response.url.split('/')
            item['title'] = html.select('.titleArticle > h1')[0].text
            item['category1'] = list[5]
            if re.findall(r'\d+',list[6]) == []:
                item['category2'] = list[6]
            item['body'] = html.select('.col-sm-11 p')[0].text
            item['abstract'] = html.select('.col-sm-11 p')[0].text
            item['pub_time'] = Util.format_time2(html.select('.articleDate')[0].text)
            if html.select('.imgArticle > img') != []:
                item['images'] = [html.select('.imgArticle > img')[0].attrs['src'],]
            yield item
        else:
            for i in html.select('.sectionTopWidget > div > div .ratio'):
                yield Request(i.attrs['href'])
            for i in html.select('.moreSectionWidget > div > div a[class="title-C20 title blu-hover"]'):
                yield Request(i.attrs['href'])
