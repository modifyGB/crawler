
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response

#将爬虫类名和name字段改成对应的网站名
class haribhoomiSpider(scrapy.Spider):
    name = 'haribhoomi'
    website_id = 943  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.haribhoomi.com/']

    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_zjx',
        'password': 'dg_zjx',
        'db': 'dg_test_source'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(DemoSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        categories = html.select("ul.sub-menu li a") if html.select("ul.sub-menu li a") else None
        for category in categories:
            category_hrefList.append(category.get('href'))

        for category in category_hrefList:
            yield scrapy.Request('https://www.haribhoomi.com%s' % category, callback=self.parse_category)

    def parse_category(self,response):
        html = BeautifulSoup(response.text, features="lxml")
        article_hrefs = []
        articles = html.select('div.list_content a') if html.select('div.list_content a') else None
        if articles:
            for href in articles:
                article_hrefs.append(href.get('href'))
            for detail_url in article_hrefs:
                yield Request('https://www.haribhoomi.com%s' % detail_url, callback=self.parse_detail)

        next_page = html.find('a', class_='page-numbers next last page-numbers') if html.find('a',class_='page-numbers next last page-numbers') else None
        try:
            next_page_href = next_page.get('href') if next_page.get('href') else None
            print(next_page_href)
            yield scrapy.Request(next_page_href, callback=self.parse)
        except AttributeError as ex1:
            pass

    def parse_detail(self, response):
        item = MyspiderItem()
        html = BeautifulSoup(response.text, features='lxml')
        item['pub_time']=html.select_one('span.convert-to-localtime').text if html.select_one('span.convert-to-localtime').text else None
        image_list = []
        imgs = html.select('div.image-wrap-article img') if html.select('div.image-wrap-article img') else None
        if imgs:
            for img in imgs:
                image_list.append(img.get('src'))
            item['images'] = image_list
        item['title']=html.select_one('div#details-page-infinite-scrolling-data h1').text
        item['abstract']=html.select_one('div#details-page-infinite-scrolling-data h2.desc_data').text
        p_list = []
        if html.select('div.story_content p'):
            all_p = html.select('div.story_content p')
            for paragraph in all_p:
                p_list.append(paragraph.text)
            body = '\n'.join(p_list)
            item['body'] = body
        yield item
