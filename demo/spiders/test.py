import re
import datetime
from datetime import datetime

# -*- coding:utf-8 -*-

# url = "https://www.centralindia.news/"
# headers = {
#     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
#     'accept-encoding': 'gzip, deflate, br',
#     'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"'
# }
# response = requests.get(url, headers=headers).text
# print(response)

# url = "https://sanmarg.in/"
# headers={
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
# }
# soup = bs(requests.get(url, headers=headers).text, features="lxml")
# print(soup)

url = 'https://sanmarg.in/entertainment/art/%e0%a4%85%e0%a4%ac-%e0%a4%ac%e0%a5%89%e0%a4%b2%e0%a5%80%e0%a4%b5%e0%a5%81%e0%a4%a1-%e0%a4%95%e0%a5%87-%e0%a4%aa%e0%a4%b0%e0%a5%8d%e0%a4%a6%e0%a5%87-%e0%a4%aa%e0%a4%b0-%e0%a4%a6%e0%a4%bf%e0%a4%96/'
splited_url = url.split("https://sanmarg.in/")[1]
print(splited_url)
category1 = splited_url.split("/", 1)[0]
category2 = None if splited_url.split("/", 2)[2] == '' else splited_url.split("/", 2)[1]
print(category2)