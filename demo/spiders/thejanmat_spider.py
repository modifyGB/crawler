
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response

#将爬虫类名和name字段改成对应的网站名
class ThejanmatSpider(scrapy.Spider):
    name = 'thejanmat_spider'
    website_id = 950 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['https://thejanmat.com/']
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cbs',
        'password': 'dg_cbs',
        'db': 'dg_test_source'
    }
    headers={
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br', 'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/89.0.4389.90 Safari/537.36} '
        }
    no_list = [
        'Video Library', 'JANMAT', 'World by Us', 'Do’s and Don’ts for a date'
    ]

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(ThejanmatSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], headers=self.headers, callback=self.parse)

    def parse(self,response):
        soup = BeautifulSoup(response.text, features="lxml")
