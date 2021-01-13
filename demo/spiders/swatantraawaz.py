import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class SwatantraawazSpider(scrapy.Spider):   # 小结：写这个爬虫的时候刚开始用了很多try，except。结果很难debug，应当最后慢慢加try，except或者用它调试。
    name = 'swatantraawaz'
    allowed_domains = ['swatantraawaz.com']
    website_id = 1043  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def start_requests(self):
        soup = BeautifulSoup(requests.get('https://www.swatantraawaz.com/').text, 'html.parser')
        for i in soup.select('.cat a'):  # 网站底部的目录，
            meta = {'category1': i.text, 'category2': None}
            url = 'https://www.swatantraawaz.com' + i.get('href')
            if re.findall('category', url):
                yield Request(url=url, meta=meta, callback=self.parse)
            else:
                self.logger.info('Wrong Url :')
                self.logger.info(url)
        for i in soup.select('.cat_txt a'):
            meta = {'category1': i.text, 'category2': None}
            url = 'https://www.swatantraawaz.com' + i.get('href')
            if re.findall('category', url):
                yield Request(url=url, meta=meta, callback=self.parse)
            else:
                self.logger.info('Wrong Url ')
                self.logger.info(url)

        for i in soup.select('#menu > ul > li')[1:-1]:   # 网站头部的目录
            meta = {'category1': i.select_one('a').text, 'category2': None}
            url = 'https://www.swatantraawaz.com' + i.select_one('a').get('href')
            try:
                yield Request(url=url, meta=meta)  # 一级目录给parse_essay
            except:
                self.logger.info('Wrong Url')
            try:
                for j in i.select('ul>li>a'):
                    meta['category2'] = j.text
                    url = 'https://www.swatantraawaz.com' + j.get('href')
                    self.logger.info('llllllllllllllllllllllll')
                    yield Request(url=url, meta=meta, callback=self.parse)
            except:
                self.logger.info('No more category2!')

    def __init__(self, time=None, *args, **kwargs):
        super(SwatantraawazSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def judge_pub_time(self, url):
        if self.time is None:
            return True
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        if re.findall('headline', url):
            tt = soup.select_one('.colort').text.split()   # 形如 ['Wednesday', '6', 'January', '2021', '02:12:12', 'PM']
            tt = tt[2]+' '+tt[1]+' '+tt[3]+' '+tt[4]+' '+tt[5]  # 形如 January 6 2021 02:12:12 PM
            tt = Util.format_time2(tt)
            if self.time is None or Util.format_time3(tt) >= int(self.time):
                return True
            else:
                return False
        elif re.findall('watchvid', url):
            tt = soup.select_one('.colort').text
            if self.time is None or Util.format_time3(tt) >= int(self.time):
                return True
            else:
                return False
        elif re.findall('photogallery', url):
            self.logger.info('Photo news have no pub_time')
            return True

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.news_sa '):
            url = 'https://www.swatantraawaz.com'+ i.select_one('.new_hed a').get('href')
            if self.judge_pub_time(url):  # 未截止，True
                response.meta['title'] = i.select_one('.new_hed a').text
                response.meta['abstract'] = i.select_one('p').text
                response.meta['images'] = ['https://www.swatantraawaz.com'+i.select_one('img').get('src')]
                yield Request(url=url, meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            nextPage = 'https://www.swatantraawaz.com'+soup.select_one('.numac ~ a').get('href')
            yield Request(nextPage, meta=response.meta, callback=self.parse)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = response.meta['abstract']
        item['images'] = response.meta['images']
        item['category2'] = response.meta['category2']
        if re.findall('headline', response.url):  # 一般新闻
            ss = ''
            for i in soup.select('.dit > p > b'):
                ss += i.text + '\n'
            try:
                ss += soup.select_one('.dit > p > span').text
            except:
                pass
            item['body'] = ss
            tt = soup.select_one('.colort').text.split()  # 形如 ['Wednesday', '6', 'January', '2021', '02:12:12', 'PM']
            tt = tt[2] + ' ' + tt[1] + ' ' + tt[3] + ' ' + tt[4] + ' ' + tt[5]  # 形如 January 6 2021 02:12:12 PM
            item['pub_time'] = Util.format_time2(tt)
        elif re.findall('watchvid',response.url):  # 视频新闻
            item['body'] = soup.select_one('.dit > p').text
            item['pub_time'] = soup.select_one('.colort').text
        else:       # 图片新闻
            item['body'] = soup.select_one('.news_saa > p').text
            item['pub_time'] = Util.format_time(0)
        return item
