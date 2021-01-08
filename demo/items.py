
import scrapy

class DemoItem(scrapy.Item):
    # 需要传进item的数据
    pub_time = scrapy.Field(serializer=str)  #文章发布时间   可用Util类中的方法实现。 否则使用"%Y-%m-%d %H:%M:%S"格式保存数据
    images = scrapy.Field()                  #body中的图片链接url   要求是字符串的list，如：["url1","url2"...]
    abstract = scrapy.Field(serializer=str)  #文章摘要   若没有则默认为文章第一句话
    body = scrapy.Field(serializer=str)      #文章内容   需要作为一个完整的字符串存入
    category1 = scrapy.Field(serializer=str) #一级分类
    category2 = scrapy.Field(serializer=str) #二级分类
    title = scrapy.Field(serializer=str)     #文章标题

    # 不需要传进item的数据
    website_id = scrapy.Field(serializer=int)
    language_id = scrapy.Field(serializer=int)
    request_url = scrapy.Field()
    response_url = scrapy.Field()
    cole_time = scrapy.Field()
    md5 = scrapy.Field()
    html = scrapy.Field() 
