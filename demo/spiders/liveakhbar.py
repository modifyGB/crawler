
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response

#将爬虫类名和name字段改成对应的网站名
class liveakhbar(scrapy.Spider):
    name = 'liveakhbar'
    website_id = 940 # 网站的id(必填)
    language_id = 1866 # 所用语言的id（该网站文章英文印地语都有）
    start_urls = ['https://www.liveakhbar.in/']
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cf',
        'password': 'dg_cf',
        'db': 'dg_test_source'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(liveakhbar, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def judge_time(self,pub_time):
        pub_time = Util.format_time3(pub_time)
        if self.time == None or pub_time >= int(self.time):
            return True
        else:
            return False

    def parse(self,response):
        meta = {}
        html = BeautifulSoup(response.text,features='lxml')
        categories_1 = html.select('ul#primary-menu li a')
        for category1 in categories_1:
            if category1.text != "HOME":
                meta['category1'] = category1.text
                yield Request(url=category1.attrs['href'],meta=meta,callback=self.parse_one)
        pass

    def parse_one(self,response):
        #补充代码
        flag = True
        html = BeautifulSoup(response.text,features='lxml')
        all_content = html.find_all('div',attrs={'class':'archive-list-post list-style'})
        for content in all_content:
            response.meta['title'] = content.select_one('div.read-title a').text
            response.meta['pub_time'] = Util.format_time2(content.find('span',attrs={'class':'item-metadata posts-date'}).text)
            response.meta['abstract'] = content.select_one('div.post-description p').text
            #补充时间截止代码
            if self.judge_time(response.meta['pub_time']):
                 yield Request(url=content.select_one('div.read-title a').attrs['href'],meta=response.meta,callback=self.parse_detail)
            else :
                self.logger.info('时间截止---------------')
                flag = False
                break
        if flag:
            try:
                next_page = html.find('a',attrs={'class':'next page-numbers'}).attrs['href']
                yield Request(url=next_page,meta=response.meta,callback=self.parse_one)
            except:
                self.logger.info("没有下一页，该目录下文章已拿完！！！！！！！！")

    def parse_detail(self,response):
        html = BeautifulSoup(response.text,features='lxml')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['category2'] = None
        item['pub_time'] = response.meta['pub_time']
        item['abstract'] = response.meta['abstract']
        body = ''
        contents = html.find('div',attrs={'class':'entry-content read-details'})
        for content in contents.select('p'):
            body += content.text
            body += '\n'
        item['body'] = body
        images = contents.find_all('figure',attrs={'class':'wp-block-image size-large'})
        item['images'] = [image.select_one('img').attrs['data-src'] for image in images]
        try:
            for img in contents.find_all('figure',attrs={'class':'wp-block-image'}):
                item['images'].append(img.select_one['img'].attrs['data-src'])
        except:
            self.logger.info("图片就这样了！！！")
        return item
