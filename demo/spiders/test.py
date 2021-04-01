import requests
from bs4 import BeautifulSoup as bs
import re

# url = "https://www.centralindia.news/"
# headers = {
#     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
#     'accept-encoding': 'gzip, deflate, br',
#     'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"'
# }
# response = requests.get(url, headers=headers).text
# print(response)

aurl = "https://www.centralindia.news/categ/%e0%a4%b0%e0%a4%be%e0%a4%9c%e0%a5%8d%e0%a4%af/"
print(re.match("https://www.centralindia.news/category/", aurl))