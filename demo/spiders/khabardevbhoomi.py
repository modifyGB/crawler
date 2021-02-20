
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import json
import requests
#将爬虫类名和name字段改成对应的网站名
class khabardvbhoomi(scrapy.Spider):
    name = 'khabardevbhoomi'
    website_id = 943 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['https://www.khabardevbhoomi.com/']
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cf',
        'password': 'dg_cf',
        'db': 'dg_test_source'
    }
    fromdata = {'action': 'td_ajax_loop',
        'loopState[sidebarPosition]':'',
        'loopState[moduleId]': '1',
        'loopState[currentPage]': '1',
        'loopState[max_num_pages]': '132',
        'loopState[atts][category_id]': '6',
        'loopState[atts][offset]': '5',
        'loopState[ajax_pagination_infinite_stop]': '0',
        'loopState[server_reply_html_data]':'' }
    post_url = 'https://www.khabardevbhoomi.com/wp-admin/admin-ajax.php?td_theme_name=Newspaper&v=8.0'

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(khabardvbhoomi, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def judge_time(self,pub_time):
        pub_time = Util.format_time2(pub_time)
        if self.time == None or Util.format_time3(pub_time) >= int(self.time):
            return True
        else:
            return False

    def parse(self,response):
        html = BeautifulSoup(response.text)
        meta = {}
        for category1 in html.select("div#td-header-menu li a"):
            if category1.text != "HOME" and category1.text != "VIDEOS":
                meta["category1"] = category1.text
                url = category1.attrs['href']
                if meta['category1'] == 'NEWS':
                    self.fromdata['loopState[atts][category_id]'] = '6'
                    yield scrapy.FormRequest(url=self.post_url,meta=meta,formdata=self.fromdata,callback=self.parse_move)
                elif meta['category1'] == "TRENDING":
                    self.fromdata['loopState[atts][category_id]'] = '10'
                    yield scrapy.FormRequest(url=self.post_url,meta=meta,formdata=self.fromdata,callback=self.parse_move)
                elif meta['category1'] =="LIFESTYLE" :
                    self.fromdata['loopState[atts][category_id]'] = '655'
                    yield scrapy.FormRequest(url=self.post_url,meta=meta,formdata=self.fromdata,callback=self.parse_move)
                else:
                    yield Request(url=url,meta=meta,callback=self.parse_jingdai)

    def parse_jingdai(self,response):
        html = BeautifulSoup(response.text)
        for info in html.select("div.td-block-span6"):
            response.meta['title'] = info.select_one('a').text
            pub_time = info.select_one('time').text
            if self.judge_time(pub_time):
                yield Request(url=info.select_one("a").attrs['href'],meta=response.meta,callback=self.parse_detail)
            else :
                break

    def parse_move(self,response):
        html = BeautifulSoup(json.loads(response.text)['server_reply_html_data'])
        flag = True
        for info in html.select('div.td-block-span6'):
            pub_time = info.select_one('time').text
            response.meta['title'] = info.select_one('a').text
            if self.judge_time(pub_time):
                yield Request(url=info.select_one("a").attrs['href'],meta=response.meta,callback=self.parse_detail)
            else:
                self.logger.info("时间截止!!!!!!")
                flag = False
                break
        if flag:
            self.logger.info("动态抓包！！！！！！")
            max_num_page = int(json.loads(response.text)['max_num_pages'])
            if int(self.fromdata['loopState[currentPage]']) <= max_num_page:
                self.fromdata['loopState[currentPage]'] = str(int(self.fromdata['loopState[currentPage]'])+1)
                yield scrapy.FormRequest(url=self.post_url,meta=response.meta,formdata=self.fromdata,callback=self.parse_move)
            else :
                self.logger.info("抓到底了！！！！")

    def parse_detail(self,response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['abstract'] = html.select_one('div.td-post-content p').text
        contents = html.select('div.td-post-content p')
        content = ''
        for content_ in contents:
            content += content_.text
            content += '\n'
        item['body'] = content
        item['pub_time'] = Util.format_time2(html.select_one('span.td-post-date time').text)
        item['category2'] = None
        item['category1'] = response.meta['category1']
        item['title'] = response.meta['title']
        item['images'] = [img.attrs['data-src'] for img in html.select('div.td-post-content picture img')]
        return item
