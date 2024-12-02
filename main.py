import requests
from bs4 import BeautifulSoup  # 用于网页抓取
import pandas as pd
import jieba
import jieba.analyse  # 用于提取关键词
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
import time

matplotlib.use("TkAgg")

# 使用Session来保持会话
session = requests.Session()


# 请求重试机制，重新请求5次
def fetch_data(url, headers, retries=5, delay=2):
    for attempt in range(retries):
        try:
            # 发送GET请求到B站API并获取响应
            response = session.get(url, headers=headers)
            # 如果返回状态码是200，表示请求成功
            if response.status_code == 200:
                return response.json()
            else:
                print(f"请求失败，状态码: {response.status_code}")
                time.sleep(delay)  # 等待一段时间后再尝试
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            time.sleep(delay)
    return None  # 如果所有请求都失败，返回None


# 爬取B站数据
def fetch_bilibili_data(url, headers):
    # 获取数据
    data = fetch_data(url, headers)

    # 如果数据请求成功
    if data:
        # 从响应数据中提取视频列表
        video_list = data['data']['list']

        # 初始化空列表以存储视频信息
        rank_list = []  # 排行
        title_list = []  # 视频标题
        play_cnt_list = []  # 播放数
        danmu_cnt_list = []  # 弹幕数
        coin_cnt_list = []  # 投币数
        like_cnt_list = []  # 点赞数
        share_cnt_list = []  # 分享数
        favorite_cnt_list = []  # 收藏数
        author_list = []  # 作者
        video_url = []  # 视频地址

        # 遍历视频列表并提取每部视频的信息
        for idx, video in enumerate(video_list):
            rank_list.append(idx + 1)  # 添加视频排行
            title_list.append(video['title'])  # 添加视频标题
            play_cnt_list.append(video['stat']['view'])  # 添加播放数
            danmu_cnt_list.append(video['stat']['danmaku'])  # 添加弹幕数
            coin_cnt_list.append(video['stat']['coin'])  # 添加投币数
            like_cnt_list.append(video['stat']['like'])  # 添加点赞数
            share_cnt_list.append(video['stat']['share'])  # 添加分享数
            favorite_cnt_list.append(video['stat']['favorite'])  # 添加收藏数
            author_list.append(video['owner']['name'])  # 添加作者名称
            video_url.append(f'https://www.bilibili.com/video/{video["bvid"]}')  # 添加视频地址

        # 使用pandas创建DataFrame，准备存储所有提取的数据
        df = pd.DataFrame({
            '排行': rank_list,
            '视频标题': title_list,
            '视频地址': video_url,
            '作者': author_list,
            '播放数': play_cnt_list,
            '弹幕数': danmu_cnt_list,
            '硬币数': coin_cnt_list,
            '点赞数': like_cnt_list,
            '分享数': share_cnt_list,
            '收藏数': favorite_cnt_list,
        })

        # 将DataFrame保存为CSV文件，不包含索引，使用utf_8_sig编码
        df.to_csv('TOP100.csv', index=False, encoding="utf_8_sig")
    pass


# 生成词云
def generate_wordcloud(text):
    # 使用 jieba 提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=100, withWeight=False)

    # 生成词云图
    words_str = ' '.join(keywords)
    wordcloud = WordCloud(
        font_path='simhei.ttf',  # 字体路径，需要一个支持中文的字体文件
        width=800,
        height=400,
        background_color='white',
        max_words=200,  # 最大显示的词数
        max_font_size=150  # 最大字体大小
    ).generate(words_str)

    # 显示词云图
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()


# 数据存储
def store_data_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf_8_sig')


def first():
    url_bilibili = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
    }
    data_TOP100 = fetch_data(url_bilibili, headers)
    if data_TOP100:
        # 从响应数据中提取视频列表
        video_list = data_TOP100['data']['list']

        # 初始化空列表以存储视频信息
        rank_list = []  # 排行
        title_list = []  # 视频标题
        play_cnt_list = []  # 播放数
        danmu_cnt_list = []  # 弹幕数
        coin_cnt_list = []  # 投币数
        like_cnt_list = []  # 点赞数
        share_cnt_list = []  # 分享数
        favorite_cnt_list = []  # 收藏数
        author_list = []  # 作者
        video_url = []  # 视频地址

        # 遍历视频列表并提取每部视频的信息
        for idx, video in enumerate(video_list):
            rank_list.append(idx + 1)  # 添加视频排行
            title_list.append(video['title'])  # 添加视频标题
            play_cnt_list.append(video['stat']['view'])  # 添加播放数
            danmu_cnt_list.append(video['stat']['danmaku'])  # 添加弹幕数
            coin_cnt_list.append(video['stat']['coin'])  # 添加投币数
            like_cnt_list.append(video['stat']['like'])  # 添加点赞数
            share_cnt_list.append(video['stat']['share'])  # 添加分享数
            favorite_cnt_list.append(video['stat']['favorite'])  # 添加收藏数
            author_list.append(video['owner']['name'])  # 添加作者名称
            video_url.append(f'https://www.bilibili.com/video/{video["bvid"]}')  # 添加视频地址

        # 使用pandas创建DataFrame，准备存储所有提取的数据
        df = pd.DataFrame({
            '排行': rank_list,
            '视频标题': title_list,
            '视频地址': video_url,
            '作者': author_list,
            '播放数': play_cnt_list,
            '弹幕数': danmu_cnt_list,
            '硬币数': coin_cnt_list,
            '点赞数': like_cnt_list,
            '分享数': share_cnt_list,
            '收藏数': favorite_cnt_list,
        })

        store_data_to_csv(df, 'TOP100.csv')

        # 生成词云
        text = ' '.join(df['视频标题'])
        generate_wordcloud(text)


def second():
    pass


# 主程序
def main():
    first()


if __name__ == "__main__":
    main()
