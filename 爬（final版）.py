from lxml import html
import re
import csv
from urllib.parse import urljoin
from datetime import datetime
import requests
import time
import random
   
# 主爬函数
def run(code,index):
    # 输入HTML文本
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
    }
    
    # 设置代理
    proxies = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890'
    }
    
    url = "https://guba.eastmoney.com/list,{code},f_{index}.html".format(index=index,code=code) if index > 1 else "https://guba.eastmoney.com/list,{code},f.html".format(code=code)
    
    # 使用代理发送请求
    html_text = requests.get(url, headers=header, proxies=proxies, timeout=10).text
    with open("guba.html","w", encoding="utf-8") as f:
        f.write(html_text)
    time.sleep(random.uniform(7,15))  # 随机等待1-2秒，避免访问过于频繁

    # 解析HTML结构
    doc = html.fromstring(html_text)

    # 提取所有帖子条目（XPath）
    post_list = doc.xpath('//table[contains(@class,"default_list")]//tr[@class="listitem"]')

    print(f"共找到 {len(post_list)} 条帖子")

    # 提取股吧名称（从页面标题）
    page_title = doc.xpath('//title/text()')[0]
    stockbar_name = re.search(r'^(.*?)\(', page_title).group(1) if page_title else ""

    # 存储结果的列表
    results = []

    
    for post in post_list:
    ##try:
        # 阅读量（XPath相对路径）
        read_count = post.xpath('.//td/div[@class="read"]/text()')[0].strip()
        
        # 回复量
        reply_count = post.xpath('.//td/div[@class="reply"]/text()')[0].strip()
        
        # 标题和链接
        title = post.xpath('.//td/div[@class="title"]/a/text()')[0].strip()
        post_url = urljoin(
            "https://guba.eastmoney.com",
            post.xpath('.//td/div[@class="title"]/a/@href')[0]
        )
        
        # 作者信息
        author_name = post.xpath('.//td/div[@class="author"]/a/text()')[0].strip()
        author_url = urljoin(
            "https://guba.eastmoney.com",
            post.xpath('.//td/div[@class="author"]/a/@href')[0]
        )
        #发帖时间
        raw_time = post.xpath('.//td/div[@class="update"]/text()')[0].strip()

        # 转换为标准datetime对象（假设年份为当前年）
        post_time = datetime.strptime(f"2025-{raw_time}", "%Y-%m-%d %H:%M")  # 根据实际年份修改
    
        # 存储结果
        results.append({
            'forum': stockbar_name,
            'read': int(read_count),
            'reply': int(reply_count),
            'title': title,
            'url': post_url,
            'author': author_name,
            'author_url': author_url,
            'post_time': post_time
        })
        
    ##except (IndexError, ValueError) as e:
        #print(f"解析失败：{str(e)}")
        #continue


    print(f"成功写入 {len(results)} 条数据到CSV文件")
    return results

#all_results = []
for m in range(8,11):
    for i in range(1, 11):
        n=str(m).zfill(6) # 用0填充到6位
        results = run(n,i)
        #all_results.extend(results)
        
        # 写入CSV文件
        with open("guba_posts_{n}_{i}.csv".format(n=n,i=i),"w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                    'forum', 'read', 'reply', 
                    'title', 'url', 'author', 'author_url','post_time'
                ])
                
            writer.writeheader()
            writer.writerows(results)


