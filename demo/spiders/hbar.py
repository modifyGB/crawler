import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests
import json


class HbarSpider(scrapy.Spider):
    name = 'hbar'
    allowed_domains = ['apkaakhbar.com']
    # start_urls = ['http://apkaakhbar.com/']
    website_id = 1059  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(HbarSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        yield Request(url='https://apkaakhbar.com/', callback=self.parse2, meta={'category1': 'Home'})
        soup = BeautifulSoup(requests.get(url='https://apkaakhbar.com/', headers=self.headers).text, 'html.parser')
        for i in soup.select('#menu-td-demo-header-menu-1 li a')[1:-1]:
            meta = {'category1': i.text}
            yield Request(url=i.get('href'), meta=meta, callback=self.parse)
            yield Request(url=i.get('href'), meta=meta, callback=self.parse_dynamic)

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('.td-big-grid-wrapper > div'):  # 两个大照片的文章
            response.meta['title'] = i.select_one('a').get('title')
            yield Request(url=i.select_one('a').get('href'), callback=self.parse_item, meta=response.meta)
        for i in soup.select('div.td-block-span6 a'):  # 静态加载的第一页，从第二页开始动态加载
            response.meta['title'] = i.get('title')
            yield Request(url=i.get('href'), callback=self.parse_item, meta=response.meta)

    def parse2(self, response):  # 主页的文章，和翻页的文章
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('.meta-info-container a'):  # 大照片新闻
            response.meta['title'] = i.get('title')
            # self.logger.info('大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大大')
            yield Request(url=i.get('href'), callback=self.parse_item, meta=response.meta)
        for i in soup.select('.td-block-span4 a'):
            response.meta['title'] = i.get('title')
            yield Request(url=i.get('href'), callback=self.parse_item, meta=response.meta)
            # self.logger.info('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        for i in range(int(soup.find('a', class_='last').text) + 1):
            nextPage = 'https://apkaakhbar.com/page/' + str(i + 1) + '/'
            html = BeautifulSoup(requests.get(nextPage, headers=self.headers).text, 'html.parser')
            for j in html.select('.td-block-span6 a'):
                response.meta['title'] = j.get('title')
                # self.logger.info('翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页翻页')
                yield Request(url=j.get('href'), callback=self.parse_item, meta=response.meta)

    def parse_dynamic(self, response):
        meta = {}
        data = {
                'action': 'td_ajax_loop',
                'loopState[sidebarPosition]': '',
                'loopState[moduleId]': '6',
                'loopState[currentPage]': '2',
                'loopState[max_num_pages]': '4',
                'loopState[atts][category_id]': '21',
                'loopState[atts][offset]': '2',
                'loopState[ajax_pagination_infinite_stop]': '0',
                'loopState[server_reply_html_data]': ''
        }
        post_url = 'https://apkaakhbar.com/wp-admin/admin-ajax.php?td_theme_name=Newspaper&v=8.0'
        max_num_pages = re.findall(r'tdAjaxLoop.loopState.max_num_pages = \d+', response.text)[-1].split()[-1]
        currentPage = 2
        #moduleId = re.findall(r"tdAjaxLoop.loopState.moduleId = '\d+'", response.text)[0].split()[-1]
        category_id = re.findall(r"'category_id':\d+", response.text)[0].split(':')[-1]
        #offset = re.findall(r'offset : \d+', response.text)[0].split()[-1]
        #stop = re.findall(r'ajax_pagination_infinite_stop = \d+', response.text)[0].split()[-1]
        data['loopState[atts][category_id]'] = category_id
        data['loopState[max_num_pages]'] = max_num_pages
        # 哭了，多加了参数结过跑不动，都怪下面这三个 id set stop
        #data['loopState[moduleId]'] = moduleId
        #data['loopState[atts][offset]'] = offset
        #data['loopState[ajax_pagination_infinite_stop]'] = stop
        if int(max_num_pages) > 1:
            for i in range(int(max_num_pages) + 1):
                i = currentPage
                currentPage += 1
                data['loopState[currentPage]'] = str(i)
                soup = BeautifulSoup(
                    json.loads(requests.post(
                        url=post_url,
                        headers=self.headers,
                        data=data).text)["server_reply_html_data"], 'html.parser')
                for j in soup.select('div.td-block-span6 a'):  # 从动态加载的第二页开始拿文章
                    # self.logger.info('动态加载htmlhtmlhtmlhtmlhtmlhtmlhtmlhtmlhtmlhtmlhtml')
                    meta['title'] = j.get('title')
                    yield Request(url=j.get('href'), callback=self.parse_item, meta=meta)
                    # self.logger.info('动态加载！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！')

    def parse_item(self, response): # 文章时间只在具体文章页面找得到
        soup = BeautifulSoup(response.text, 'html.parser')
        tt = Util.format_time2(soup.select_one('.td-post-date').text)
        if self.time == None or Util.format_time3(tt) >= int(self.time):
            item = DemoItem()
            item['images'] = [i.get('src') for i in soup.select('article img')[:-3]]
            item['title'] = response.meta['title']
            item['category1'] = response.meta['category1']
            item['category2'] = None
            item['pub_time'] = tt
            abstract = ''
            for i in soup.select('strong '):
                abstract += i.text
            item['abstract'] = abstract
            item['body'] = soup.findChildren(class_='td-post-content')[0].get_text()
            return item

        else:
            self.logger.info('时间截止')
