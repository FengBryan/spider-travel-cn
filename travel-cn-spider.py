import time
from string import Template

import pandas as pd
import query_string
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from user_agent import generate_user_agent

db_url = Template('mysql+pymysql://${user}:${password}@${host}:${port}/${db}')
db_user = 'root'  # 数据库用户, 需更改
db_user_password = 'password'  # 数据库密码, 需更改
db_host = '127.0.0.1'  # 数据库地址, 需更改
db_port = '3306'  # 数据库端口, 需更改
db_name = 'test'  # 数据库名称, 需更改

db_engine = create_engine(db_url.substitute(
    user=db_user, password=db_user_password, host=db_host, port=db_port, db=db_name))

start_time = time.time()
current_page = 1  # 第一页开始
url = 'http://travel.cntour.cn/travels/list.aspx'

headers = {
    'User-Agent': generate_user_agent()
}
strhtml = requests.get(url, headers=headers, params={'page': current_page})

soup = BeautifulSoup(strhtml.text, features='html.parser')
pager = soup.find('div', id='pager2').find_all('span')

print('获取总页数')
total_page = 0

if len(pager) <= 0:
    total_page = 1
else:
    total_page = query_string.parse(
        pager[len(pager) - 1].find('a').get('href')).get('page')

all_items = []
print('共有: ', total_page, '页')

for page_number in range(1, int(total_page) + 1):
    current_page = page_number
    random_headers = {
        'User-Agent': generate_user_agent()
    }
    res = requests.get(url, headers=headers, params={'page': current_page})
    current_view = requests.get(
        url, headers=headers, params={'page': current_page})
    print('处理第', current_page, '页')
    data = soup.find('div', id='graders_list')
    all_items.extend(data.find_all('ul'))

print('处理结束, 正在储存')
filtred_data = filter(lambda tag: not tag.find(
    'li', attrs=['class', 'conditions']), all_items)
struct_data = map(lambda tag: {
    'title': tag.find('a', attrs=['class', 'title']).text,
    'author': tag.find('div', attrs=['class', 'author']).text,
    'pic': tag.find('img').get('src')
}, filtred_data)

final_data = list(struct_data)
result_data_frame = pd.DataFrame(
    final_data, columns=('title', 'author', 'pic'))

result_data_frame.to_sql(
    'tour_list_test' + str(time.time_ns()), db_engine, index=False)
end_time = time.time()

print('🚀结束:', ' 共处理', len(final_data), '条数据')
print('🕙:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
print('⏱️总耗时:', str(end_time - start_time), '秒')
