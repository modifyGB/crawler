import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class cnnphilippinesSpider(scrapy.Spider):
    name = 'cnnphilippines'
    website_id = 449 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.cnnphilippines.com/']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_rht',
        'password' : 'dg_rht',
        'db' : 'dg_test'
    }

    def parse(self, response):
        html = BeautifulSoup(response.text)
        if response.url == 'https://www.cnnphilippines.com/':
            for i in html.select('#topNavbar > ul > li > a')[1:7]:
                yield Request('http://www.cnnphilippines.com'+i.attrs['href'])
        elif re.findall(r'https://www.cnnphilippines.com/\S+?/\d+/\d+/\d+/\S+',response.url) != []:
            item = DemoItem()
            list = response.url.split('/')
            item['title'] = html.select('.title')[0].text
            item['category1'] = list[3]
            if re.findall(r'\d+',list[4]) == []:
                item['category2'] = list[4]
            item['body'] = ''
            flag = False
            for i in html.select('#content-body-244757-498257 > p'):
                item['body'] += (i.text+'\n')
                if i.text != '' and flag == False:
                    flag = True
                    item['abstract'] = i.text
            if html.select('.dateLine > p') != []:
                item['pub_time'] = Util.format_time2(html.select('.dateLine > p')[0].text)
            elif html.select('.dateString') != []:
                item['pub_time'] = Util.format_time2(html.select('.dateString')[0].text)
            if html.select('.margin-bottom-15 img') != []:
                item['images'] = [html.select('.margin-bottom-15 img')[0].attrs['src'],]
            yield item
        else:
            for i in html.select('section.row a'):
                yield Request('https://www.cnnphilippines.com'+i.attrs['href'])
            for i in html.select('section[class="row container-padding-10"] a'):
                yield Request('https://www.cnnphilippines.com'+i.attrs['href'])