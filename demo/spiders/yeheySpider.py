import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


#将爬虫类名和name字段改成对应的网站名
class yehey(scrapy.Spider):
    name = 'yehey'
    website_id = 1225 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://yehey.com/']
    sql = { # sql配置
        'host' : '192.168.235.162',
        'user' : 'dg_gfy',
        'password' : 'dg_gfy',
        'db' : 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(yehey, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        soup=BeautifulSoup(response.text,'lxml')
        url=soup.select_one('li#menu-item-5581>a').get('href')
        meta['category1']=soup.select_one('li#menu-item-5581>a').text
        meta['category2']=''
        yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    def parse_category2(self,response):

        ex='<li id="menu-item-.*?menu-item menu-item-type-taxonomy menu-item-object-category menu-item-has-children menu-item.*?href="(.*?)"'
        list=re.findall(ex,response.text,re.S)#二级目录
        ex1='<li id="menu-item-.*?menu-item menu-item-type-taxonomy menu-item-object-category menu-item.*?href="(.*?)"'
        list1=re.findall(ex1,response.text,re.S)#所有的url
        list1_not_in_list = [i for i in list1 if i not in list]#最底层的url:三级目录，如果没有，则二级目录
        ex3='https://yehey.com/category/(.*?)/.*?'
        for url in list1_not_in_list:
            response.meta['category2']=re.findall(ex3,url,re.S)
            yield scrapy.Request(url,meta=response.meta,callback=self.parse_category3)
    
    def parse_category3(self,response):
        #处理静态加载出来的page1
        soup=BeautifulSoup(response.text,'lxml')
        news_list=soup.find_all('h2',class_='entry-title th-text-md th-mb-0')
        for news in news_list:
            new_url=news.find('a').get('href')
            yield scrapy.Request(new_url,meta=response.meta,callback=self.parse_detail)

        page_text=response.text
        ex='<script type="text/javascript">.*?currentday%22%3A%22(.*?)%22%2C%22'
        if(re.findall(ex,page_text,re.S)):
            yield scrapy.Request(response.url,meta=response.meta,callback=self.parse_dynamic)
        



    def parse_dynamic(self,response):
        #动态加载出来的page2-。。
        dynamic_url='https://yehey.com/?infinity=scrolling'
        page_text=response.text
        ex='<script type="text/javascript">.*?currentday%22%3A%22(.*?)%22%2C%22'
        start=re.findall(ex,page_text,re.S)
        fir=response.url.split('/')[-2]
        data={
            'page': '2',
            'currentday': str(start),
            'query_args[category_name]': fir
        }
        dic_url=requests.post(dynamic_url,data).json()['postflair']
        for news_url in dic_url.keys():
            yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_detail)


        for page in range(3,100):
            if (requests.post(dynamic_url,data).json()['currentday']):
                dynamic_category=fir
                dynamic_currentday=requests.post(dynamic_url,data).json()['currentday']
                
                data={
                    'page': str(page),
                    'currentday': dynamic_currentday,
                    'query_args[category_name]': dynamic_category
                }
                dic_url=requests.post(dynamic_url,data).json()['postflair']
                for news_url in dic_url.keys():
                    if self.time==None or Util.format_time3(time)>=int(self,time):
                       yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_detail)
                    else:
                        self.logger.info('时间截止')

                
    

    def parse_detail(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']
        item['title']=soup.find('h1',class_='entry-title th-mb-0 sm:th-text-8xl th-text-4xl').text.strip() if soup.find('h1',class_='entry-title th-mb-0 sm:th-text-8xl th-text-4xl') else None

        item['body'] = ''#不能忘记初始化
        body_list=soup.find('div',class_='entry-content th-content').select('p') if soup.find('div',class_='entry-content th-content').select('p')else None
        for body in body_list:
            item['body'] += body.text.strip()
            item['body'] +='\n'

        item['images']=''
        image_list=soup.find('div',class_='entry-content th-content').select('a>img')if soup.find('div',class_='entry-content th-content').select('a>img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images']+=image
                item['images']+='\n'

 

        item['abstract']=soup.find('div',class_='entry-content th-content').select('p')[0].text if soup.find('div',class_='entry-content th-content').select('p') else None
    
        pub=soup.find('time',class_='entry-date published').get('datetime') if soup.find('time',class_='entry-date published') else None
        pub=re.split('T|\\+',str(pub))
        pub=pub[0]+' '+pub[1] 
        item['pub_time']=pub

        yield item