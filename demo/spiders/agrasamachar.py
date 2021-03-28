import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import time
import datetime

#author:詹婕妤

class AgrasamacharSpider(scrapy.Spider):
    name = 'agrasamachar'
    website_id = 1150  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    allowed_domains = ['www.agrasamachar.com']
    start_urls = ['https://www.agrasamachar.com/',]
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_zjy',
        'password': 'dg_zjy',
        'db': 'dg_test_source'
    }
    month = {'जनवरी': 1, 'फ़रवरी': 2, 'मार्च': 3, 'अप्रैल': 4, 'मई': 5, 'जून': 6, 'जुलाई': 7, 'अगस्त': 8,
             'सितंबर': 9, 'अक्तूबर': 10, 'नवंबर': 11, 'दिसंबर': 12}
    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(AgrasamacharSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time
    def parse(self, response):
        soup = bs(response.text,'html.parser')
        for i in soup.find_all(class_='post-title entry-title'):
            url = i.find('a').get('href')
            self.logger.info(url)
            yield scrapy.Request(url,callback=self.parse_news)
        if soup.find(class_='blog-pager-older-link'):
            next_url = soup.find('a',class_='blog-pager-older-link').get('href')
            pub_time1 = soup.find_all(class_='date-header')[-1].find('span').text
            pub_time = time.strftime("%Y-%m-%d %H:%M:%S",datetime.datetime(int(pub_time1.split()[-1]), self.month[pub_time1.split()[1]],int(pub_time1.split()[0])).timetuple())
            self.logger.info(pub_time)
            if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                self.logger.info(next_url)
                yield scrapy.Request(next_url,callback=self.parse)
            else:
                self.logger.info('时间截止')

    def parse_news(self,response):
        item = DemoItem()
        soup = bs(response.text,'html.parser')
        title = soup.find(class_='post-title entry-title').text.strip()
        images = [i.find('img').get('src') for i in soup.find_all(class_='tr-caption-container')] if soup.find(class_='tr-caption-container') else []
        body = soup.find(class_='post-body entry-content').text
        pub_time = soup.find(class_='date-header').find('span').text
        item['title'] = title
        item['images'] = images
        item['pub_time'] = time.strftime("%Y-%m-%d %H:%M:%S",datetime.datetime(int(pub_time.split()[-1]), self.month[pub_time.split()[1]],int(pub_time.split()[0])).timetuple())
        item['body'] = body.replace('\xa0','\n').strip()
        item['abstract'] = item['body'].split('\n')[0]
        item['category1'] = None
        item['category2'] = None
        self.logger.info(item)
        yield item
