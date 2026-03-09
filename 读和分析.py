import statistics
from lxml import html
import re
import csv
from urllib.parse import urljoin
from datetime import datetime
import requests
import time
import random
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties

# 设置中文字体
font_path = "C:\\Windows\\Fonts\\simhei.ttf"  # SimHei 黑体字体路径
if os.path.exists(font_path):
    chinese_font = FontProperties(fname=font_path)
    rcParams['font.family'] = chinese_font.get_name()
else:
    print("警告: 未找到中文字体文件，中文可能无法正常显示")

# 读取所有CSV文件并合并数据
def load_all_csv_data():
    # 获取当前目录下所有的CSV文件
    csv_files = glob.glob("guba_posts_*.csv")
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    all_results = []
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            # 将post_time列转换为datetime类型
            df['post_time'] = pd.to_datetime(df['post_time'])
            
            # 将DataFrame转换为字典列表
            file_results = df.to_dict('records')
            all_results.extend(file_results)
            print(f"成功读取 {csv_file}，包含 {len(file_results)} 条数据")
        except Exception as e:
            print(f"读取 {csv_file} 时出错: {str(e)}")
    
    print(f"总共读取了 {len(all_results)} 条帖子数据")
    return all_results

# 加载所有数据
all_results = load_all_csv_data()

# 如果找不到数据，给出提示并退出
if not all_results:
    print("未找到任何帖子数据，请先运行爬虫脚本生成CSV文件")
    exit()

# 提取阅读量和回复量数据集
reads = [post['read'] for post in all_results]
replies = [post['reply'] for post in all_results]

def get_statistics(data: list) -> dict:
    """计算完整的描述性统计量"""
    try:
        quantiles = statistics.quantiles(data, n=4)
        return {
            'N': len(data),
            'Mean': statistics.mean(data),
            'Std': statistics.stdev(data) if len(data) > 1 else 0,
            'Min': min(data),
            'Q1': quantiles[0],
            'Median': quantiles[1],
            'Q3': quantiles[2],
            'Max': max(data)
        }
    except statistics.StatisticsError as e:
        print(f"统计计算错误：{str(e)}")
        return None

def print_stat_table(stats: dict, name: str):
    """格式化输出统计表格"""
    print(f"\n{name}统计分析结果：")
    print("{:<8} {:<10}".format('指标', '值'))
    print("-"*20)
    print("{:<8} {:<10,.0f}".format('样本数', stats['N']))
    print("{:<8} {:<10,.2f}".format('平均值', stats['Mean']))
    print("{:<8} {:<10,.2f}".format('标准差', stats['Std']))
    print("{:<8} {:<10,.0f}".format('最小值', stats['Min']))
    print("{:<8} {:<10,.2f}".format('25分位', stats['Q1']))
    print("{:<8} {:<10,.2f}".format('中位数', stats['Median']))
    print("{:<8} {:<10,.2f}".format('75分位', stats['Q3']))
    print("{:<8} {:<10,.0f}".format('最大值', stats['Max']))

# 计算并输出统计结果
read_stats = get_statistics(reads)
if read_stats:
    print_stat_table(read_stats, "阅读量")

reply_stats = get_statistics(replies)
if reply_stats:
    print_stat_table(reply_stats, "回复量")

# ==========================================
print("\n" + "="*50)
print("功能1: 发帖时间在一天24小时中的分布")
print("="*50)

# 随机抽样200条帖子，如果总数少于200则使用全部
sample_size = min(200, len(all_results))
sampled_posts = random.sample(all_results, sample_size)

print(f"从总共 {len(all_results)} 条帖子中随机抽取了 {sample_size} 条进行时间分析")

# 提取所有帖子的小时信息
hour_data = []
for post in sampled_posts:
    if post.get('post_time'):  # 确保post_time存在且不为None
        hour_data.append(post['post_time'].hour)

# 统计每个小时的发帖数量
hour_counts = Counter(hour_data)

# 准备24小时的完整数据
all_hours = list(range(24))
hour_distribution = [hour_counts.get(hour, 0) for hour in all_hours]

# 绘制柱状图
plt.figure(figsize=(14, 7))
bars = plt.bar(all_hours, hour_distribution, color='skyblue')

# 添加图表标题和轴标签
plt.title('发帖时间分布', fontsize=16, fontproperties=chinese_font)
plt.xlabel('小时', fontsize=14, fontproperties=chinese_font)
plt.ylabel('帖子数量', fontsize=14, fontproperties=chinese_font)
plt.xticks(all_hours, [f"{h}:00" for h in all_hours])
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 标记最高的柱子
max_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0
max_count = hour_counts.most_common(1)[0][1] if hour_counts else 0
for i, bar in enumerate(bars):
    if i == max_hour:
        bar.set_color('orange')
        plt.text(i, max_count + 1, f'max: {max_count}',
                 ha='center', va='bottom', fontweight='bold')
    
    # 在每个柱子上方显示帖子数量
    plt.text(i, bar.get_height() + 0.3, str(int(bar.get_height())),
             ha='center', va='bottom')

plt.tight_layout()
plt.savefig('hourly_distribution.png')
plt.show()

# 按时间段统计
time_periods = {
    '凌晨 (0-6点)': sum(hour_counts.get(h, 0) for h in range(0, 6)),
    '上午 (6-12点)': sum(hour_counts.get(h, 0) for h in range(6, 12)),
    '下午 (12-18点)': sum(hour_counts.get(h, 0) for h in range(12, 18)),
    '晚上 (18-24点)': sum(hour_counts.get(h, 0) for h in range(18, 24))
}

# 绘制饼图
plt.figure(figsize=(10, 8))
labels = [f"{period} ({count}posts)" for period, count in time_periods.items()]
sizes = list(time_periods.values())
colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
explode = (0.05, 0.05, 0.05, 0.05)  # 稍微突出各个部分

plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
        shadow=True, startangle=90, explode=explode)
plt.axis('equal')  # 确保饼图是圆的
plt.title('发帖时间段分布', fontsize=16, fontproperties=chinese_font)
plt.savefig('time_period_distribution.png')
plt.show()

# 打印发帖时间统计结果
print("\n发帖时间段分布统计:")
print("-" * 40)
print("{:<15} {:<10} {:<10}".format('时间段', '帖子数量', '占比'))
print("-" * 40)
total_posts = sum(time_periods.values())
for period, count in time_periods.items():
    percentage = (count / total_posts * 100) if total_posts else 0
    print("{:<15} {:<10} {:<10.2f}%".format(period, count, percentage))

# 输出发帖高峰时段
print(f"\n发帖高峰时段: {max_hour}:00-{max_hour+1}:00，共 {max_count} 条帖子")

# ==========================================
print("\n" + "="*50)
print("功能2: 发帖量排名前三的作者")
print("="*50)

# 统计每个作者的发帖量
author_counts = Counter()
for post in all_results:
    author_counts[post['author']] += 1

# 获取发帖量排名前三的作者
top_authors = author_counts.most_common(10)

# 输出排名结果
print("\n发帖量排名前10名的作者:")
print("-" * 40)
print("{:<6} {:<15} {:<10} {:<10}".format('排名', '作者', '发帖数量', '占比'))
print("-" * 40)

total_posts = len(all_results)
for rank, (author, count) in enumerate(top_authors, 1):
    percentage = (count / total_posts * 100) if total_posts else 0
    print("{:<6} {:<15} {:<10} {:<10.2f}%".format(rank, author, count, percentage))

# 绘制前十名作者的柱状图
top_10 = author_counts.most_common(10)
authors = [author for author, _ in top_10]
counts = [count for _, count in top_10]

plt.figure(figsize=(12, 6))
bars = plt.bar(range(len(authors)), counts, color='lightgreen')

# 高亮前三名
for i in range(min(3, len(bars))):
    bars[i].set_color(['gold', 'silver', '#CD7F32'][i])  # 金、银、铜色

plt.title('发帖量排名前10名的作者', fontsize=16, fontproperties=chinese_font)
plt.xlabel('作者', fontsize=14, fontproperties=chinese_font)
plt.ylabel('发帖数量', fontsize=14, fontproperties=chinese_font)
plt.xticks(range(len(authors)), authors, rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 在柱子上添加数值标签
for i, count in enumerate(counts):
    plt.text(i, count + 0.5, str(count), ha='center')

plt.tight_layout()
plt.savefig('top_authors.png')
plt.show()

# 分析前三名作者的发帖时间特征
print("\n前三名作者的发帖时间特征:")
for i, (author, total) in enumerate(top_authors[:3], 1):
    # 获取该作者的所有帖子
    author_posts = [post for post in all_results if post['author'] == author]
    
    # 统计该作者的发帖时间分布
    author_hours = [post['post_time'].hour for post in author_posts if hasattr(post['post_time'], 'hour')]
    hour_freq = Counter(author_hours)
    
    # 找出最常发帖的时间
    if hour_freq:
        favorite_hour, max_posts = hour_freq.most_common(1)[0]
        
        # 时间段分析
        time_segments = {
            '凌晨 (0-6点)': sum(1 for h in author_hours if 0 <= h < 6),
            '上午 (6-12点)': sum(1 for h in author_hours if 6 <= h < 12),
            '下午 (12-18点)': sum(1 for h in author_hours if 12 <= h < 18),
            '晚上 (18-24点)': sum(1 for h in author_hours if 18 <= h < 24)
        }
        favorite_segment = max(time_segments.items(), key=lambda x: x[1])
        
        print(f"\n第{i}名: {author} (共发帖 {total} 条)")
        print(f"  - 最喜欢发帖的时间: {favorite_hour}:00 (共 {max_posts} 条, 占比 {max_posts/total:.1%})")
        print(f"  - 最活跃的时间段: {favorite_segment[0]} (共 {favorite_segment[1]} 条, 占比 {favorite_segment[1]/total:.1%})")

# ==========================================
print("\n" + "="*50)
print("功能3: 阅读量与回复量的关系分析")
print("="*50)

# 计算阅读量和回复量的相关系数
if len(reads) == len(replies) and len(reads) > 1:
    # 使用pandas计算相关系数
    df_corr = pd.DataFrame({'阅读量': reads, '回复量': replies})
    correlation = df_corr.corr().iloc[0, 1]
    print(f"\n阅读量与回复量的皮尔逊相关系数: {correlation:.4f}")
    
    # 判断相关性强度
    if abs(correlation) > 0.7:
        strength = "强"
    elif abs(correlation) > 0.3:
        strength = "中等"
    else:
        strength = "弱"
    
    # 判断相关性方向
    direction = "正" if correlation > 0 else "负"
    
    print(f"这表示阅读量和回复量之间存在{strength}{direction}相关关系")

# 绘制散点图
plt.figure(figsize=(10, 8))
plt.scatter(reads, replies, alpha=0.5, c='blue')
plt.title('阅读量与回复量的关系', fontsize=16, fontproperties=chinese_font)
plt.xlabel('阅读量', fontsize=14, fontproperties=chinese_font)
plt.ylabel('回复量', fontsize=14, fontproperties=chinese_font)
plt.grid(True, linestyle='--', alpha=0.7)

# 添加趋势线
if len(reads) > 1:
    z = np.polyfit(reads, replies, 1)
    p = np.poly1d(z)
    plt.plot(sorted(reads), p(sorted(reads)), "r--", linewidth=2)
    
    # 添加趋势线方程
    equation = f"y = {z[0]:.6f}x + {z[1]:.2f}"
    plt.annotate(equation, xy=(0.05, 0.95), xycoords='axes fraction', 
                fontsize=12, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

plt.tight_layout()
plt.savefig('read_reply_correlation.png')
plt.show()

print("\n分析完成！所有图表已保存。")